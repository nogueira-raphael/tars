# tars-core

The Diagnostics bounded context — database-agnostic execution plan, schema, and lock analysis. Imported directly only by `services/mcp-server` (never by `services/orchestrator`, see `docs/adr/0010` at the repository root).

See `/docs/architecture/domain-model.md` for the internal layout and dependency rules, and `/docs/adr/0007-normalized-diagnostic-schema.md` for the most important undefined contract in this package right now.

This is the first service to build — see the build order in `/docs/architecture/domain-model.md`.
