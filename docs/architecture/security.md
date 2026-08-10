# Security Model

## Credential storage

Database credentials and LLM provider API keys are encrypted at rest with Fernet (symmetric encryption, `cryptography` package), using a key generated on first run and persisted in the relevant service's local storage volume. No master password is required from the user.

This is the same pattern used by comparable self-hosted tools: pgAdmin4 without a master password derives its encryption key from its own configuration database; n8n uses a locally-generated `N8N_ENCRYPTION_KEY`. It is not a production secrets vault — anyone with access to the Docker volume can decrypt. That trade-off is accepted deliberately, consistent with the Web UI having no authentication in this phase (see below).

**Two separate local SQLite stores, not one shared file:**

- The **MCP Server's** store holds database credentials and the connection registry. It is the only component with direct database driver access, so it's the only one that needs this data.
- The **Orchestrator's** store holds chat history, session state, and LLM provider API keys.

Keeping these separate avoids SQLite locking/concurrency issues across containers and keeps the MCP Server the sole owner of database credentials — the Orchestrator's store never contains anything that could reach a target database.

## MCP Server authentication

A shared bearer token, generated on first `docker compose up` and stored alongside the encryption key, gates all access to the MCP Server — uniformly, for every client, including external standalone ones (e.g. Claude Desktop connecting directly). There is no unauthenticated path.

## Web UI authentication

None, at least initially. This is consistent with the local-first, single-user default deployment. The practical implication: the Web UI's port must be published as `127.0.0.1:<port>` in `docker-compose.yml`, never `0.0.0.0` — it should never be reachable from outside the local machine by default.

## The approval gate

`execute_sql` calls are classified mutating/read-only by automatic SQL parsing (`sqlglot`), not by the caller (Orchestrator/LLM) self-declaring intent — trusting a caller's self-declaration is weaker, and doesn't depend on the LLM "remembering" to set a flag correctly.

Two legs, two mechanisms:

1. **MCP Server ↔ Orchestrator** — [MCP elicitation](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/). As of the 2026-07-28 protocol revision, elicitation is not a live back-channel: the server returns an `InputRequiredResult` plus an opaque `request_state` token instead of executing; the client resolves the input and re-invokes the same tool with the answer and token attached. Using elicitation here (rather than a purely Orchestrator-side gate) also protects anyone using the MCP Server standalone — e.g. from Claude Desktop — which an Orchestrator-only gate would not cover.
2. **Orchestrator ↔ Web UI** — SSE (server pushes an "approval needed" event) + a plain POST (the user's decision comes back). The Web UI is not an MCP client and can't receive elicitation directly, so this leg needs its own mechanism regardless of what happens on the MCP Server leg.

The Orchestrator relays the elicitation request from the MCP Server to the Web UI over SSE, waits for the POST response, then re-calls the original tool with the approval + `request_state` token attached — at which point the MCP Server actually executes.

## Known limitation, deliberately out of scope for now

The current connection direction is Orchestrator → MCP Server (Orchestrator dials in). A future hosted/"cloud" deployment (Orchestrator + Web UI hosted, MCP Server local next to the database) would need this inverted — the MCP Server dialing out via a relay, or a tunnel — if the MCP Server sits behind NAT/a firewall, which is the common case. No design work is happening on this; it's recorded so it isn't forgotten if the topic comes back.
