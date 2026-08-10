# 7. A single normalized schema for plans, schema graphs, and lock trees

**Status:** Accepted (shape not yet defined) — 2026-08-07

## Context

`explain_query`, schema exploration, and `active_sessions`/`locks` each return data meant to be rendered as a visualization in the Web UI (and, later, potentially via MCP Apps `ui://` resources). Each database engine has its own native representation for these — Postgres's `EXPLAIN (FORMAT JSON)` output looks nothing like SQL Server's XML showplan.

## Decision

`tars-core` defines its own normalized intermediate representation for all three: execution plans, schema graphs, and lock trees. Each provider (Postgres, SQL Server, and any future engine) translates its native output into this shared shape before it leaves `tars-core`. The Web UI's renderers (React Flow-based) only ever consume this normalized shape, never engine-specific output.

## Rationale

Without this, every new database engine added later would also require new rendering logic in the Web UI — quietly breaking the "database agnostic" promise at exactly the point where it matters most (the primary differentiator, diagnostics as a visual object). Normalizing once in `tars-core` keeps the Web UI, and any future MCP Apps widget, engine-agnostic by construction.

## Consequences

- This is the most load-bearing undefined contract in the codebase right now — `execution_plan.py`, `schema_graph.py`, and `locks.py` in `tars-core/domain/` can't be meaningfully implemented until it's designed.
- The exact field-level shape (node types, cost/row-estimate fields, tree vs. graph structure) is **deliberately not designed yet** — it's scoped as part of actually building `tars-core`, not as an upfront spec exercise. See `docs/architecture/overview.md`'s open items.
- Whoever designs it needs to look at both Postgres's `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` and SQL Server's showplan XML/`sys.dm_exec_query_plan` output before finalizing field names, to avoid a shape that quietly favors one engine's model over the other's.
