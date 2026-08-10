# 1. PostgreSQL and SQL Server as the first two database providers

**Status:** Accepted — 2026-08-07

## Context

TARS aims to be database-agnostic, but the first version can't support every engine at once. The starting set needs to prove the `DatabaseProvider` abstraction actually generalizes, not just work for one convenient case.

## Decision

The first two providers are **PostgreSQL** and **SQL Server** — not PostgreSQL and MySQL.

## Rationale

MySQL is close enough to PostgreSQL in semantics that the abstraction would look easy far longer than it actually is; the real seams (execution plan formats, system-view/DMV terminology, catalog dialects) wouldn't show up until a third, more different engine was added — delaying discovery of problems in the core abstraction. SQL Server forces those differences to surface immediately: its execution plan representation, its DMVs (`sys.dm_exec_requests` vs. `pg_stat_activity`), and its catalog access are meaningfully different from Postgres's.

## Consequences

- Building the SQL Server provider costs more upfront than a Postgres+MySQL pairing would have.
- The `DatabaseProvider` port, once it works for both, is much more likely to generalize to a third engine (Oracle, MySQL, Snowflake, ...) later without a redesign.
- SQL Server introduces a real environment limitation: no native ARM64 image, so the demo container runs via Rosetta emulation on Apple Silicon (accepted, documented in `docs/architecture/tech-stack.md`).
