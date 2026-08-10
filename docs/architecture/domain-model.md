# Domain Model & Repository Structure

Pattern: Hexagonal / Ports & Adapters, paired with DDD tactical patterns — applied strongly where there's real domain complexity, deliberately thin elsewhere. Not applied uniformly as ceremony. See `docs/adr/0010-ddd-hexagonal-monorepo-structure.md` for the reasoning.

## Bounded contexts

### `services/tars-core` — Diagnostics

The real domain model. DDD applied strongly.

- `domain/` — zero dependency on any framework or driver.
  - `connection.py` — `Connection` (entity), `ConnectionId` (value object).
  - `query.py` — `Query` (entity), `QueryFingerprint` (value object).
  - `execution_plan.py` — `ExecutionPlan` (aggregate). The normalized plan-graph schema lives here — field shape not finalized yet, see the open item in `overview.md`.
  - `schema_graph.py` — `SchemaGraph` (aggregate), `Table` / `Column` / `ForeignKey` (value objects).
  - `locks.py` — `LockTree` (aggregate), `BlockingSession` (value object).
  - `index_recommendation.py` — recommendation-only, no apply path (see `docs/adr/` on index suggestions).
  - `ports.py` — abstract interfaces: `DatabaseProvider`, `ConnectionRepository`, `SqlClassifier`.
- `application/` — use cases that orchestrate domain objects; no business logic of their own, only depend on `domain/ports.py`, never a concrete adapter.
  - `explain_query.py`, `analyze_index_health.py`, `inspect_locks.py`, `classify_statement.py`.
- `infrastructure/` — concrete implementations of the ports.
  - `providers/postgres.py` (`psycopg3`), `providers/sqlserver.py` (`mssql-python`).
  - `sql_classifier.py` (`sqlglot`-based `SqlClassifier` implementation).
  - `connection_store.py` (Fernet + SQLite `ConnectionRepository` implementation).
- `tests/unit/` — exercise `domain/` and `application/` against fake ports, no real database required.
- `tests/integration/` — exercise the real providers against the demo Postgres/SQL Server containers.

### `services/mcp-server` — protocol adapter (deliberately thin)

No `domain/` folder on purpose. If a change here starts to need one, the logic belongs in `tars-core` instead.

- `tools/` — one module per MCP tool; each calls a `tars-core` use case and translates the result into an MCP tool response.
- `auth.py` — validates the shared bearer token (see `docs/architecture/security.md`).
- `server.py` — MCP SDK wiring, Streamable HTTP transport.

### `services/orchestrator` — Conversation

Its own bounded context, with its own domain model — separate from `tars-core`, and `orchestrator` never imports `tars-core` directly (it only reaches diagnostics through an MCP tool call, via `mcp-server`).

- `domain/`
  - `chat_session.py` — `ChatSession` (aggregate): a connection + an LLM provider + a message history. Each chat session binds its own pair; multiple concurrent sessions are supported.
  - `message.py`.
  - `approval_request.py` — the state machine for a pending elicitation (pending / approved / denied).
  - `ports.py` — `ModelProvider`, `McpClient`.
- `application/`
  - `send_message.py` — the thin tool-calling loop.
  - `resolve_approval.py`.
- `infrastructure/`
  - `llm/` — one adapter per provider (`anthropic.py`, `openai.py`, `google.py`, `ollama.py`), all official SDKs, no multi-provider framework.
  - `mcp_client.py` — Streamable HTTP MCP client, handles elicitation responses.
  - `api/` — FastAPI routes + the SSE endpoint the Web UI consumes.
  - `session_store.py` — Fernet + SQLite store for chat history, sessions, and LLM API keys.

### `web` — feature-sliced, not layer-sliced

```
web/src/
├── features/          # one folder per feature, each roughly mirrors a backend bounded context
│   ├── chat/
│   ├── connections/
│   ├── plan-viewer/    # React Flow-based execution plan renderer
│   ├── schema-explorer/
│   └── approvals/
├── shared/             # shadcn/ui components, design tokens, API client
└── app/                # routing, providers, entry point
```

`src-tauri/` holds the Tauri native shell — same web bundle, packaged as an installable app, alongside (not replacing) the containerized page served by Nginx.

## Dependency rule

`domain/` never imports `application/` or `infrastructure/`. `application/` only imports `domain/ports.py` interfaces, never a concrete implementation. This is what makes `tars-core`'s unit tests runnable without a real Postgres or SQL Server instance — swap the `DatabaseProvider` port for a fake.

This includes third-party libraries, not just other layers of this codebase: `domain/` types are plain stdlib `dataclasses`, never Pydantic — see `docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md`. Pydantic is still used in the project, just never inside `domain/`.

## Build order

`tars-core` → `mcp-server` (validated against a generic MCP client, no `orchestrator`/`web` needed) → SQL Server provider (second engine proves the abstraction) → `orchestrator` → `web` last.
