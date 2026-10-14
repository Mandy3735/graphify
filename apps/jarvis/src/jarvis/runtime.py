"""Single active PostgreSQL application process and production role checks."""

import asyncio

from sqlalchemy import text

from jarvis.config import Settings
from jarvis.db import Database

LOCK = 0x4A4152564953


class RuntimeGuard:
    def __init__(self, db: Database, cfg: Settings):
        self.db, self.cfg = db, cfg
        self.connection = None
        self.monitor = None
        self.healthy = cfg.environment != "production"

    async def check_role(self, connection):
        unsafe = await connection.scalar(
            text("""
            SELECT EXISTS (SELECT 1 FROM pg_roles WHERE
                pg_has_role(current_user, oid, 'MEMBER') AND
                (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
            OR has_schema_privilege(current_user, 'public', 'CREATE')
            OR has_database_privilege(current_user, current_database(), 'CREATE')
            OR has_database_privilege(current_user, current_database(), 'TEMPORARY')
            OR EXISTS (SELECT 1 FROM pg_namespace WHERE nspname='public'
                AND pg_has_role(current_user, nspowner, 'MEMBER'))
            OR EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='public' AND pg_has_role(current_user, c.relowner, 'MEMBER'))
            OR has_table_privilege(current_user, 'public.audit_events', 'UPDATE')
            OR has_table_privilege(current_user, 'public.audit_events', 'DELETE')
            OR has_table_privilege(current_user, 'public.audit_events', 'TRUNCATE')
            OR has_table_privilege(current_user, 'public.alembic_version', 'UPDATE')
            OR has_table_privilege(current_user, 'public.alembic_version', 'INSERT')
            OR has_table_privilege(current_user, 'public.alembic_version', 'DELETE')
        """)
        )
        if unsafe:
            raise RuntimeError("Production requires a restricted non-owner database role")

    async def acquire(self, failed):
        if self.db.engine.dialect.name != "postgresql":
            return
        self.connection = await self.db.engine.connect()
        try:
            version = await self.connection.scalar(text("SELECT version_num FROM alembic_version"))
            if version != "0005":
                raise RuntimeError("Apply the current JARVIS migrations before startup")
            if self.cfg.environment == "production":
                await self.check_role(self.connection)
            locked = await self.connection.scalar(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK}
            )
            if not locked:
                raise RuntimeError("Another JARVIS application worker owns this database")
            pid = await self.connection.scalar(text("SELECT pg_backend_pid()"))
            await self.connection.commit()
            self.healthy = True
            self.monitor = asyncio.create_task(self.watch(pid, failed))
        except BaseException:
            await self.connection.close()
            self.connection = None
            self.healthy = False
            raise

    async def watch(self, pid: int, failed):
        try:
            while True:
                await asyncio.sleep(2)
                async with asyncio.timeout(3):
                    assert self.connection is not None
                    held = await self.connection.scalar(
                        text("""
                        SELECT pg_backend_pid()=:pid AND EXISTS (
                            SELECT 1 FROM pg_locks WHERE locktype='advisory'
                            AND pid=:pid AND granted AND classid=:high AND objid=:low)
                    """),
                        {"pid": pid, "high": LOCK >> 32, "low": LOCK & 0xFFFFFFFF},
                    )
                    if not held:
                        raise RuntimeError("Lease lost")
                    await self.connection.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            self.healthy = False
            await failed()

    async def close(self):
        self.healthy = False
        if self.monitor is not None:
            self.monitor.cancel()
            await asyncio.gather(self.monitor, return_exceptions=True)
        if self.connection is not None:
            try:
                if not self.connection.invalidated:
                    await self.connection.execute(
                        text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK}
                    )
                    await self.connection.commit()
            except Exception:
                await self.connection.invalidate()
            finally:
                await self.connection.close()
                self.connection = None
