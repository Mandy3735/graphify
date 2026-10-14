-- Apply as the migration/database owner after upgrading to the current revision.
-- psql --set=runtime_role=jarvis_runtime_app --file=runtime-role.sql DATABASE
-- This creates a NEW role with no password. Provision authentication separately.
\set ON_ERROR_STOP on
\if :{?runtime_role}
\else
  \echo 'Set runtime_role to a new jarvis_runtime_* name'
  \quit 1
\endif
SELECT :'runtime_role' ~ '^jarvis_runtime_[a-z0-9_]{1,40}$'
  AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:'runtime_role') AS valid \gset
\if :valid
\else
  \echo 'Expected a NEW jarvis_runtime_* role; existing roles are never modified'
  \quit 1
\endif
BEGIN;
CREATE ROLE :"runtime_role" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOREPLICATION NOBYPASSRLS NOINHERIT;
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'runtime_role') \gexec
SELECT format('REVOKE CREATE, TEMPORARY ON DATABASE %I FROM PUBLIC', current_database()) \gexec
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"runtime_role";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"runtime_role";
REVOKE UPDATE, DELETE ON audit_events FROM :"runtime_role";
REVOKE INSERT, UPDATE, DELETE ON alembic_version FROM :"runtime_role";
-- No TRUNCATE, REFERENCES, TRIGGER, DDL, ownership, role membership or admin grants.
ALTER ROLE :"runtime_role" SET search_path = public, pg_catalog;
COMMIT;
