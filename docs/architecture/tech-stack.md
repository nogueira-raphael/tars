# Technology Stack

Chosen 2026-08-07/10, favoring what's already the de facto standard for each layer over novelty.

## Infrastructure

| Layer | Choice | Notes |
|---|---|---|
| Containers | Docker + Docker Compose | Install is `docker compose up`. |
| Backend image | `python:3.13-slim` | Multi-stage builds. |
| Web UI image | `node:22-alpine` build → static Nginx | SPA build, no Node runtime in production. |
| Postgres (demo) | `postgres:17` | Onboarding/demo environment. |
| SQL Server (demo) | `mcr.microsoft.com/mssql/server` | No native ARM64 image — runs via Rosetta emulation on Apple Silicon, accepted as a known limitation. |

## Backend (Python — `tars-core`, `mcp-server`, `orchestrator`)

| Layer | Choice | Why |
|---|---|---|
| Packaging | `uv` | Replaced pip/poetry/pyenv as the 2026 default; one shared workspace lockfile across all three services. |
| Lint/format | `ruff` | Same team as `uv` (Astral). |
| Type-checking | `mypy` (strict) | |
| Web framework | FastAPI | Orchestrator's HTTP/SSE surface. |
| MCP | Official `mcp` Python SDK, Streamable HTTP transport | SSE transport was deprecated by the MCP spec in favor of Streamable HTTP; stdio reserved for standalone clients. |
| Postgres driver | `psycopg3` (async) | Unified sync/async API, richer feature set (LISTEN/NOTIFY) — raw throughput isn't the bottleneck for a diagnostics tool. |
| SQL Server driver | `mssql-python` (Microsoft's official driver, GA Nov 2025) | Replaces `pyodbc` — bundles the ODBC driver, pyodbc-compatible API, native Apple Silicon support. |
| ORM | None | Not even SQLAlchemy — see `docs/adr/0002-...` for why. |
| Validation | Pydantic v2 | Ships with FastAPI and the MCP SDK. |
| SQL classification | `sqlglot` | Covers both Postgres and T-SQL dialects; used to classify `execute_sql` calls as mutating or not. |
| LLM providers | Official SDKs only: `anthropic`, `openai`, `google-genai`; Ollama via its OpenAI-compatible REST API | No multi-provider framework — see `docs/adr/0003-thin-custom-orchestrator-not-langgraph.md`. |
| Internal HTTP client | `httpx` (async) | Orchestrator → MCP Server calls. |
| Credential encryption | `cryptography` (Fernet) | Same mechanism for DB credentials and LLM API keys, two separate local SQLite stores — see `docs/architecture/security.md`. |
| Tests | `pytest` + `pytest-asyncio` | |

## Web UI (TypeScript / React)

| Layer | Choice | Why |
|---|---|---|
| Build | Vite (SPA) | No SSR/API-route needs — Next.js would pay complexity for features unused here. |
| Package manager | `pnpm` | |
| UI components | shadcn/ui (Radix or Base UI) + Tailwind | "Copy, don't install" — code lives in-repo, forkable, fits open-source-first. |
| Native packaging | Tauri (not Electron) | ~5-15MB installer using the system WebView vs. Electron's ~80-120MB bundling Chromium; the preferred distribution channel, alongside (not replacing) the container-served page. |
| Diagrams (plans, schema graphs, lock trees) | `@xyflow/react` (React Flow) | Standard React node/edge library; Dagre/ElkJS layout integrations for auto-laid-out plan trees. |
| Charts/timelines | Recharts | Fast to ship for the MVP; revisit with visx/D3 if bespoke visuals are needed later. |
| SQL editor | CodeMirror 6 | ~50kB modular vs. Monaco's 5-10MB; what comparable DB tools (Prisma Studio, etc.) use. |
| Chat streaming | SSE (native `EventSource`), not WebSocket | Chat is a one-way "server streams the response" pattern; approvals go over a separate POST — no full-duplex need. |
| State/data | TanStack Query + Zustand | Query for HTTP, Zustand for light session/chat state. |
| Lint/format | Biome | Replaces ESLint + Prettier. |
| Tests | Vitest + Testing Library + Playwright | |

## Explicitly not used, and why

- **SQLAlchemy / any ORM** for talking to target databases — the diagnostic queries (`pg_stat_activity`, SQL Server DMVs, `EXPLAIN`) are engine-specific with no useful cross-dialect abstraction to gain; the real abstraction is `tars-core`'s own `DatabaseProvider` port.
- **LangGraph / LangChain** for the Orchestrator's tool-calling loop — the actual need is a linear loop plus a human-approval gate, not multi-agent branching; a heavy framework would cost more than it returns.
- **Electron** for the native Web UI shell — Tauri gives the same outcome with a far smaller footprint for this category of tool.
- **WebSocket** for Orchestrator↔Web UI streaming — SSE is simpler and scales better for the one-way pattern this actually is.
