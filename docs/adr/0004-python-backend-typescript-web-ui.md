# 4. Python for the whole backend, TypeScript/React for the Web UI

**Status:** Accepted — 2026-08-07

## Context

`tars-core`, `mcp-server`, and `orchestrator` each need a language. The Web UI needs one too, and needs to run in a browser regardless of what the backend uses.

## Decision

Python for all three backend services (sharing one `uv` workspace). TypeScript + React for the Web UI.

## Rationale

The MCP Python SDK is first-class and mature. The database-tooling ecosystem in Python (`psycopg`, `mssql-python`, `sqlglot`, and the wider data-engineering world) is mature and matches the target audience's (DBAs, data engineers) existing skills, which also lowers the bar for community contribution. Keeping all three backend services in one language means one workspace, one lockfile, one CI toolchain for the entire backend — a real simplicity win for an early-stage open-source project with a small core team.

The alternative considered was TypeScript end-to-end (Node backend + React frontend) for tighter type-sharing between frontend and backend (tRPC-style DX). That's a real but secondary benefit, achievable anyway via FastAPI's OpenAPI generation feeding a TypeScript client — it didn't outweigh Python's ecosystem fit for the diagnostics domain itself.

## Consequences

- The Web UI talks to the Orchestrator over HTTP/SSE as a genuinely separate service in a different language — never a shared in-process call.
- Type-sharing between backend and frontend goes through generated OpenAPI clients, not native shared types.
- Backend distribution (`docs/architecture/tech-stack.md`) uses `uv`; the "Python is hard to distribute" concern is neutralized by containerizing everything (`docs/adr/0005-...`) — end users never install Python directly.
