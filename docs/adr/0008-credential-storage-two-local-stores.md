# 8. Encrypted local credential storage, two separate stores

**Status:** Accepted — 2026-08-07

## Context

Database connection credentials and LLM provider API keys both need to be stored somewhere persistent. The OS keychain (`keyring` package) was the first instinct, but `mcp-server` and `orchestrator` run inside Docker containers, which generally can't reach the host's Secret Service (Linux) or Keychain (macOS).

## Decision

Encrypt both kinds of secret at rest with Fernet (`cryptography` package), using a key generated on first run and persisted in the service's own Docker volume. **Two separate SQLite stores, not one shared file:** the MCP Server's store holds database credentials + the connection registry; the Orchestrator's store holds chat history/sessions + LLM API keys.

## Rationale

`keyring` was ruled out because the container boundary makes host-keychain access impractical in the general (cross-platform) case. The chosen pattern — app-managed encryption with a locally-generated key, no master password required — mirrors what comparable self-hosted tools already do: pgAdmin4 without a master password derives its key from its own config database; n8n uses a locally-generated `N8N_ENCRYPTION_KEY`. Splitting into two stores (rather than one shared SQLite file mounted into both containers) avoids SQLite's known fragility under concurrent access from separate processes/containers, and keeps the MCP Server as the sole component that ever touches a database credential — the Orchestrator's store never contains anything that could reach a target database, even indirectly.

## Consequences

- Anyone with access to the relevant Docker volume can decrypt its secrets — this is accepted as "local convenience, not a production vault," consistent with the Web UI having no authentication (`docs/architecture/security.md`).
- A shared bearer token (see `docs/architecture/security.md`) is the actual access-control boundary for the MCP Server, not the encryption itself.
- If TARS ever adds a genuine multi-user or hosted mode, this storage model would need to be revisited — noted as a known limitation, not solved now.
