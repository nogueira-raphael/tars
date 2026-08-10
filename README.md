# Project TARS

An open-source, database-agnostic runtime for database engineering through AI, automation, and modern dev tools.

Most AI database tools convert natural language into SQL. TARS focuses on database *engineering*: why is this query slow, which indexes are missing or unused, why did the optimizer choose this plan, which sessions are blocking others. It presents that as structured visualizations — execution plan graphs, schema graphs, lock trees — not just narrated text.

> **Status:** early scaffold. Architecture is decided; implementation hasn't started. See `docs/` before writing code.

## Principles

- **Open source first** — MIT licensed, community-extensible.
- **Database agnostic** — a common abstraction over PostgreSQL, SQL Server, and (later) other engines.
- **IDE agnostic** — MCP server, web UI, CLI, and IDE plugins as peers over the same runtime.
- **AI optional** — the diagnostic core is fully deterministic; AI is a conversational layer on top, not a requirement.
- **Local first** — credentials never leave your machine; AI services only see what you explicitly allow.

## Repository layout

```
services/tars-core/     # Diagnostics domain: providers, plan/schema/lock models, index analysis
services/mcp-server/    # Exposes tars-core as MCP tools
services/orchestrator/  # Thin LLM tool-calling loop + approval gate, talks to mcp-server over MCP
web/                    # React/TypeScript UI — Tauri app and/or containerized page
docker/                 # docker-compose.yml (base) + docker-compose.demo.yml (sample databases)
docs/architecture/      # current-state architecture reference
docs/adr/               # architecture decision records — the "why" behind everything above
```

See `docs/architecture/overview.md` for the full picture, and `AGENTS.md` if you're an AI coding agent working in this repo.

## Status / build order

`tars-core` → `mcp-server` → SQL Server provider → `orchestrator` → `web`. Nothing is implemented yet; this scaffold exists so the structure and conventions are settled before the first line of domain code is written.

## License

MIT — see `LICENSE`.
