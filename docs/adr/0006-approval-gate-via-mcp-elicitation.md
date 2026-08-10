# 6. Approval gate implemented via MCP elicitation + SSE relay

**Status:** Accepted — 2026-08-07, mechanism detailed 2026-08-07 (round 2 of grilling)

## Context

Mutating operations (writes via `execute_sql`) need a human-in-the-loop confirmation before executing. The Web UI (where the human is) is one hop away from the MCP Server (where the operation would run) — the Orchestrator sits between them, and the Web UI is not itself an MCP client.

## Decision

Two mechanisms, one per hop:

1. **MCP Server ↔ Orchestrator:** [MCP elicitation](https://modelcontextprotocol.io/extensions/apps/overview). As of the 2026-07-28 protocol revision, this is not a live back-channel — the server returns `InputRequiredResult` + a `request_state` token instead of executing, and the client (Orchestrator) re-invokes the same tool with the answer and token once it has one.
2. **Orchestrator ↔ Web UI:** an SSE event pushed to the Web UI (approval needed) + a plain POST back (the user's decision).

Classification of a given `execute_sql` call as mutating is automatic — `sqlglot`-based SQL parsing (Postgres and T-SQL dialects) — not a flag the caller (Orchestrator/LLM) sets itself.

## Rationale

Elicitation was chosen over a purely Orchestrator-side gate specifically because it protects anyone using the MCP Server **standalone** (e.g. from Claude Desktop), which an Orchestrator-only gate would not cover — consistent with treating standalone MCP Server usage as a first-class scenario. The Web UI leg still needs its own mechanism regardless, since it isn't an MCP client and can't receive elicitation directly. Automatic classification (rather than caller self-declaration) was chosen because trusting the caller is weaker and doesn't depend on the LLM reliably setting a flag correctly.

## Consequences

- `sqlglot` is a hard dependency of `tars-core`'s `SqlClassifier` implementation.
- `mcp-server`'s `execute_sql` tool handler needs to know how to construct and return `InputRequiredResult` + `request_state`, and how to resume execution once the Orchestrator re-invokes it with an answer.
- The Orchestrator's `ApprovalRequest` domain object needs a state machine (pending → approved/denied) and must correlate the SSE-relayed approval back to the correct `request_state` token.
- Index suggestions stay recommendation-only (no auto-apply path), which keeps this gate's scope limited to operations TARS itself executes, not every diagnostic recommendation it makes.
