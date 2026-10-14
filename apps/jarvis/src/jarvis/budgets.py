"""Durable pre-call admission. Unknown outcomes retain their full estimate."""

import asyncio
from contextlib import asynccontextmanager
from decimal import ROUND_CEILING, Decimal

from sqlalchemy import select

from jarvis.config import Settings
from jarvis.db import Database, ProviderBudgetDay, ProviderCall, audit, now


class BudgetExceeded(Exception):
    code = "provider_budget_unavailable"


def microusd(amount: float | Decimal) -> int:
    return int((Decimal(str(amount)) * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


class ProviderBudget:
    def __init__(self, db: Database, cfg: Settings):
        self.db, self.cfg = db, cfg
        self.lock = asyncio.Lock()

    def token_cost(self, model: str, input_tokens: int, output_tokens: int = 0) -> int:
        price = self.cfg.pricing.get(model)
        if price is None:
            raise BudgetExceeded("Pricing required before a live provider call")
        return int(
            (
                Decimal(input_tokens) * Decimal(str(price[0]))
                + Decimal(output_tokens) * Decimal(str(price[1]))
            ).to_integral_value(rounding=ROUND_CEILING)
        )

    def operation_cost(self, kind: str, model: str) -> int:
        estimate = self.cfg.provider_operation_costs.get(f"{kind}:{model}")
        if estimate is None:
            raise BudgetExceeded("Operation estimate required before a live provider call")
        return microusd(estimate)

    async def reserve(self, kind: str, model: str, estimate: int) -> str:
        if estimate < 0 or len(model) > 200:
            raise BudgetExceeded()
        day = now().date().isoformat()
        async with self.lock, self.db.sessions.begin() as session:
            if self.db.engine.dialect.name == "postgresql":
                from sqlalchemy.dialects.postgresql import insert
            else:
                from sqlalchemy.dialects.sqlite import insert
            await session.execute(
                insert(ProviderBudgetDay)
                .values(day=day, charged_microusd=0)
                .on_conflict_do_nothing(index_elements=["day"])
            )
            total = await session.scalar(
                select(ProviderBudgetDay).where(ProviderBudgetDay.day == day).with_for_update()
            )
            assert total is not None
            if total.charged_microusd + estimate > microusd(self.cfg.provider_daily_budget_usd):
                raise BudgetExceeded("Daily provider admission budget reached")
            total.charged_microusd += estimate
            call = ProviderCall(
                day=day,
                actor_id=str(self.cfg.actor_id),
                kind=kind,
                model=model,
                reserved_microusd=estimate,
                charged_microusd=estimate,
            )
            session.add(call)
            await session.flush()
            audit(
                session,
                str(self.cfg.actor_id),
                "provider.reserved",
                {"call_id": call.id, "kind": kind, "model": model, "microusd": estimate},
            )
            return call.id

    async def finish(self, key: str, actual: int | None, usage: dict, state: str):
        async with self.lock, self.db.sessions.begin() as session:
            call = await session.scalar(
                select(ProviderCall).where(ProviderCall.id == key).with_for_update()
            )
            assert call is not None
            if call.state != "RESERVED":
                return
            total = await session.scalar(
                select(ProviderBudgetDay).where(ProviderBudgetDay.day == call.day).with_for_update()
            )
            assert total is not None
            charged = actual if actual is not None else call.reserved_microusd
            total.charged_microusd += charged - call.charged_microusd
            call.charged_microusd, call.usage, call.state = charged, usage, state
            audit(
                session,
                str(self.cfg.actor_id),
                "provider.settled",
                {"call_id": key, "state": state, "microusd": charged},
            )

    @asynccontextmanager
    async def operation(self, kind: str, model: str):
        key = await self.reserve(kind, model, self.operation_cost(kind, model))
        try:
            yield key
        except BaseException:
            await asyncio.shield(self.finish(key, None, {}, "UNCERTAIN"))
            raise
        else:
            await self.finish(key, None, {}, "ESTIMATED")

    async def status(self) -> dict:
        day = now().date().isoformat()
        async with self.db.sessions() as session:
            total = await session.get(ProviderBudgetDay, day)
            calls = list(
                await session.scalars(
                    select(ProviderCall)
                    .where(ProviderCall.actor_id == str(self.cfg.actor_id), ProviderCall.day == day)
                    .order_by(ProviderCall.created_at.desc())
                    .limit(30)
                )
            )
            return {
                "day_utc": day,
                "limit_usd": self.cfg.provider_daily_budget_usd,
                "charged_estimate_usd": (total.charged_microusd if total else 0) / 1_000_000,
                "calls": [
                    {
                        "id": c.id,
                        "kind": c.kind,
                        "model": c.model,
                        "state": c.state,
                        "usage": c.usage,
                        "charged_estimate_usd": c.charged_microusd / 1_000_000,
                    }
                    for c in calls
                ],
            }
