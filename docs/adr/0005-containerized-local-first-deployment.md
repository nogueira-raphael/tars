# 5. Containerized, local-first deployment via Docker Compose

**Status:** Accepted — 2026-08-07

## Context

TARS's "Local First" principle requires that database credentials stay under the user's control. The runtime also needs to be easy to install across platforms without requiring users to manage Python/Node environments themselves.

## Decision

Every service (`mcp-server`, `orchestrator`, `web` when containerized) ships as a Docker image, orchestrated by Docker Compose. Installation is `docker compose up`. Two compose files: a base one (assumes the user already has databases to point at) and `docker-compose.demo.yml`, an overlay adding pre-seeded sample Postgres/SQL Server containers for onboarding.

## Rationale

Containerizing removes the need for end users to install Python or Node at all, which also neutralizes the usual "Python is hard to distribute" concern (`docs/adr/0004-...`). It keeps the MCP Server — the only component with database credentials — running on the user's own machine or network, which is a practical requirement, not just a principle: most real target databases (local dev instances, on-prem servers behind a VPN/firewall) simply aren't reachable from anywhere but the local network.

## Consequences

- The demo overlay's sample databases seed automatically via container init scripts, using known sample schemas (pagila/dvdrental for Postgres, an AdventureWorks subset for SQL Server) rather than a synthetic dataset or a manual seed step.
- A future hosted/"cloud" backend is not blocked architecturally (the MCP Server is already an independently-deployable component with its own auth), but isn't in scope now — see `docs/architecture/security.md`'s note on connection direction.
- The Web UI additionally ships as a native Tauri app (`docs/adr/0009-...`), which runs on the host outside the Compose network — this requires the Orchestrator's port to be published to `127.0.0.1`, not just reachable inside the Compose network.
