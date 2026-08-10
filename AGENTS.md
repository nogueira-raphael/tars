# AGENTS.md

Instructions for AI coding agents (Claude Code, Cursor, Codex, or any other) working in this repository. Human contributors should read `CONTRIBUTING.md` and `docs/architecture/` instead — this file is optimized for an agent starting a session with no memory of prior ones.

## What this project is

TARS is an open-source, database-agnostic runtime for database engineering through AI, automation, and dev tools — diagnostics (execution plans, index health, locks/sessions), not natural-language-to-SQL. Full rationale: `docs/architecture/overview.md`. Every non-obvious decision has a matching record in `docs/adr/` — read the relevant ADR before assuming a decision was arbitrary or before proposing to change it.

## Repository shape

Monorepo. Three Python services in one `uv` workspace, one TypeScript/React web app.

```
services/tars-core/     # Diagnostics bounded context — the real domain model. DDD applied strongly.
services/mcp-server/    # MCP protocol adapter. Deliberately thin — no domain layer of its own.
services/orchestrator/  # Conversation bounded context — its own domain model, separate from tars-core.
web/                    # Vite + React + TypeScript, packaged as a Tauri app and/or a container.
docker/                 # docker-compose.yml (base) + docker-compose.demo.yml (sample databases).
docs/architecture/      # current-state architecture docs.
docs/adr/               # why things are the way they are, one decision per file, never edited after acceptance.
```

Full structure and the dependency rules: `docs/architecture/domain-model.md` and `docs/adr/0010-ddd-hexagonal-monorepo-structure.md`.

**Build order** (see `docs/adr/0010-...`): `tars-core` first, validated with unit tests (fake providers) and integration tests against the demo Postgres container. Then `mcp-server`, validated against a generic MCP client — no `orchestrator` or `web` needed yet. Then the SQL Server provider. Then `orchestrator`. `web` last. Don't jump ahead of this order without asking — later pieces depend on contracts (the normalized diagnostic schema, the Orchestrator↔Web UI API) that are intentionally not finalized until the piece before them is built.

## Hard rules — do not cross without asking

- `services/orchestrator` never imports `tars-core` directly. It only reaches diagnostics functionality through an MCP tool call, via `services/mcp-server`. This is load-bearing, not a style preference — it's what keeps the MCP Server usable standalone by other MCP clients (Claude Desktop, etc.), a core design goal.
- Inside `tars-core` and `orchestrator`: `domain/` never imports `application/` or `infrastructure/`. `application/` only imports `domain/ports.py` interfaces, never a concrete adapter. This is what makes `tars-core`'s unit tests runnable without a real Postgres/SQL Server.
- `mcp-server` gets no `domain/` folder. If you find yourself wanting to put business logic there, it belongs in `tars-core` instead — `mcp-server` should stay a thin, deterministic translation layer between the MCP protocol and `tars-core` use cases.
- Database credentials live only in `tars-core`'s local store (Fernet-encrypted SQLite). `orchestrator` has its own separate local store for chat history/sessions/LLM API keys. Never merge these into one shared file — see `docs/adr/0008-credential-storage-two-local-stores.md` for why.
- No ORM. Not SQLAlchemy, not anything else, for talking to target databases (Postgres via `psycopg3`, SQL Server via `mssql-python`, both behind the `DatabaseProvider` port). See `docs/adr/0002-...` and `docs/architecture/tech-stack.md` for the reasoning — this has already been debated, don't relitigate it in a PR.
- `domain/` uses plain stdlib `dataclasses`, never Pydantic (`BaseModel` or otherwise) — not even for convenience. This was violated once already in the initial scaffold and had to be fixed; see `docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md`. Pydantic belongs at infrastructure/interface boundaries (`mcp-server`'s future tool-argument validation, `orchestrator`'s future FastAPI models) — never in `domain/`, in either service.

## Toolchain (once code exists)

- Python: `uv` for everything (env, deps, run). `uv sync` at the repo root syncs the whole workspace. `uv run pytest services/<name>/tests` to test one service. `uv run ruff check .` / `uv run ruff format .` for lint/format. `uv run mypy .` for type-checking (strict mode, see root `pyproject.toml`).
- TypeScript (`web/`): `pnpm install`, `pnpm biome check .` for lint/format, `pnpm vitest` for unit tests, `pnpm playwright test` for e2e.
- Style: `STYLE_GUIDE.md` — Google's Python and TypeScript style guides as the base, with this repo's deviations called out explicitly. Linters (`ruff`, `mypy`, `biome`) enforce what they can; the style guide covers judgment calls they don't (naming semantics, comment discipline, module layout).

## Working conventions

- Every module in `domain/` and `application/` should be understandable without knowing FastAPI, the MCP SDK, or any specific database driver — if it isn't, it's probably infrastructure code that leaked upward.
- Don't invent the normalized diagnostic schema (`ExecutionPlan`, `SchemaGraph`, `LockTree` shapes) or the Orchestrator↔Web UI API contract on your own initiative — both are explicitly deferred design steps (see `docs/adr/0007-...` and the open item in `docs/architecture/overview.md`). Flag it and ask rather than guessing a shape that becomes load-bearing by accident.
- Stub files in this initial scaffold are intentionally empty (docstring + `NotImplementedError` where a signature is already known, otherwise just a module docstring). Don't fill them with speculative logic — implement one use case at a time, starting with `tars-core`, per the build order above.
