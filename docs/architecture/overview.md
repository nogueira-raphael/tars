# Architecture Overview

## Vision

TARS is a vendor-neutral platform for database engineering — inspecting, diagnosing, and optimizing databases — usable from IDEs, web applications, CLIs, automation pipelines, and AI assistants alike. It aims to become the common runtime that developers, DBAs, IDEs, and AI assistants use to understand and manage databases, the way Docker became the runtime for containers.

## What makes TARS different

Most AI database tools convert natural language into SQL. TARS focuses on database engineering: why is this query slow, which indexes are missing or unused, why did the optimizer choose this plan, which sessions are blocking others. Answers come back as structured visualizations (execution plan graphs, schema graphs, lock trees), not narrated text.

**Primary differentiator (MVP scope):** diagnostics as a visual object. MCP tools return structured, normalized data; the Web UI renders it directly — the "TARS presents structured visualizations" thesis as a tangible product, not a promise.

**Deferred, not MVP:**
- Execution plan diffing (comparing two plans to explain a regression) — needs history/snapshot infrastructure that doesn't exist yet.
- Approval-gate impact preview (estimated time/size before approving a mutating operation) — needs per-operation estimation logic.
- Visualization via [MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview) (`ui://` resources) so standalone MCP clients (Claude Desktop, VS Code, etc.) get the same rendered visualizations without going through TARS's own Web UI — a fast-follow, not sized yet.

## Core principles

- **Open source first** (MIT).
- **Database agnostic** — PostgreSQL and SQL Server first, chosen specifically because their dialects and system views differ enough to stress-test the abstraction early.
- **IDE agnostic** — MCP server, Web UI, and (later) CLI/IDE plugins as peer clients of the same runtime.
- **AI optional** — `tars-core` and `mcp-server` are fully deterministic. Only `orchestrator` calls an LLM. Someone can drive `mcp-server` directly with zero AI involvement and get full diagnostic value.
- **Local first** — database credentials never leave the user's machine unless explicitly allowed; the only network egress in the default topology is the Orchestrator's call to whichever LLM provider is configured.

## Runtime topology

```
┌─────────────────────────── docker compose / local machine ───────────────────────────┐
│                                                                                         │
│   Web UI  ──chat · SSE──▶  Orchestrator  ──tool calls · MCP (streamable HTTP+token)──▶ │
│  (Nginx container         (Python,             MCP Server (Python, tars-core)          │
│   or Tauri app)            thin loop)                    │                             │
│                                 │                          ├──SQL──▶ PostgreSQL         │
│                                 │                          └──SQL──▶ SQL Server         │
└─────────────────────────────────┼──────────────────────────────────────────────────────┘
                                   │  prompt + tool schemas · HTTPS
                                   ▼  (only traffic leaving the machine)
                            LLM Provider (Claude / OpenAI / Gemini / Ollama)
```

Only the MCP Server has database drivers and credentials. Only the Orchestrator crosses the machine boundary, and only to send messages + tool schemas to the configured LLM — never raw credentials. The MCP Server can also be used standalone by other MCP clients (Claude Desktop, Cursor, etc.), bypassing the Orchestrator and Web UI entirely — this is why tool logic lives only in `tars-core`/`mcp-server`, never duplicated in the Orchestrator.

## MCP tool surface (v1)

| Tool | Purpose | Can trigger the approval gate? |
|---|---|---|
| `list_schemas` / `list_tables` | Schema exploration | No |
| `explain_query` | Execution plan, returned in the normalized schema | No |
| `index_health` | Missing/unused/redundant indexes — recommendation only, no auto-apply | No |
| `active_sessions` / `locks` | Active sessions, blocking tree | No |
| `execute_sql` | The only tool that can write. Read-only by default | Yes, if not read-only |

## Approval gate

`execute_sql` calls are classified mutating/read-only by automatic SQL parsing (`sqlglot`, covers Postgres and T-SQL), not caller self-declaration. Mutating calls trigger [MCP elicitation](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/): the MCP Server returns an `InputRequiredResult` + `request_state` token instead of executing; the Orchestrator relays that to the Web UI over SSE, waits for the user's approval via POST, then re-invokes the same tool with the answer + token attached — only then does it execute. Full detail: `docs/adr/0006-approval-gate-via-mcp-elicitation.md`.

## Further reading

- `docs/architecture/domain-model.md` — bounded contexts, DDD/hexagonal rules, repository layout.
- `docs/architecture/tech-stack.md` — concrete technology choices per layer.
- `docs/architecture/security.md` — credential storage, auth, the two-leg approval gate in detail.
- `docs/adr/` — one record per major decision, with the reasoning and alternatives considered.

## Open at the architecture level

- Final field-level shape of the normalized diagnostic schema (`ExecutionPlan`, `SchemaGraph`, `LockTree`) — deferred to when `tars-core` is actually built, not decided upfront.
- Orchestrator↔Web UI API contract (endpoint names, SSE event format, POST payload shapes) — same, deferred to that build step.
- Real project/package names (repo name, PyPI name if `tars-core` is published separately, container image names, Tauri installer name) — deliberately deferred to closer to publication. Note: bare "tars" is already taken on PyPI, npm, and as a GitHub user/org; `tars-core` specifically is free on PyPI as of 2026-08-10.
