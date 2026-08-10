# mcp-server

Exposes `tars-core` as MCP tools over Streamable HTTP. Deliberately thin — see `/AGENTS.md` and `/docs/adr/0010-ddd-hexagonal-monorepo-structure.md` for why this service has no domain layer of its own.

Can be used standalone by any MCP client (Claude Desktop, Cursor, etc.), independent of `services/orchestrator` and `web/` — this is why all diagnostic logic lives in `tars-core`, never duplicated here.

Second service to build, after `tars-core` — see `/docs/architecture/domain-model.md`'s build order. Validate it against a generic MCP client before `services/orchestrator` exists.
