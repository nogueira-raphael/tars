# 2. No ORM — abstraction lives in `tars-core`'s own `DatabaseProvider` port

**Status:** Accepted — 2026-08-07

## Context

TARS needs to talk to multiple database engines through a common interface. SQLAlchemy (or a similar ORM/Core query builder) is the default reach for "abstract over multiple SQL dialects" in Python.

## Decision

No ORM — not SQLAlchemy, not anything else — for talking to target databases. Each engine gets a native driver (`psycopg3` for Postgres, `mssql-python` for SQL Server) behind `tars-core`'s own `DatabaseProvider` port. TARS's own internal state (connection registry, chat history, plan snapshots) also skips an ORM, using plain `sqlite3`/`aiosqlite`.

## Rationale

SQLAlchemy's value is abstracting dialect for generic CRUD. TARS's queries are the opposite of generic: `pg_stat_activity`, SQL Server DMVs, `EXPLAIN` output — all engine-specific, with no cross-dialect translation to gain. The real abstraction TARS needs is at the level of "get me the execution plan" or "get me blocking sessions," not at the level of SQL syntax — and that's exactly what the `DatabaseProvider` port already provides. Adding an ORM underneath would be an abstraction layer with no abstraction to do.

## Consequences

- Each provider implementation talks to its engine natively and is free to use engine-specific features (Postgres's `hypopg`, SQL Server's `sys.dm_exec_query_plan`) without fighting a query builder.
- No ORM migration/session-management machinery to configure or reason about.
- Internal state storage (SQLite) is simple enough that an ORM wouldn't reduce code either — direct SQL against a small, stable local schema.
