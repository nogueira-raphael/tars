# docker

Two compose files, per `/docs/adr/0005-containerized-local-first-deployment.md`:

- `docker-compose.yml` — base: `mcp-server`, `orchestrator`, `web-ui`. Assumes the user already has databases to point at. Orchestrator's port must publish to `127.0.0.1` (not `0.0.0.0`) so a natively-installed Tauri app on the host can reach it.
- `docker-compose.demo.yml` — overlay adding sample PostgreSQL (`pagila`/`dvdrental`) and SQL Server (AdventureWorks subset) containers, seeded automatically via container init scripts. No manual seed step.

**Not written yet.** Both files depend on services that don't exist yet (`mcp-server`, `orchestrator`, `web`) — see the build order in `/docs/architecture/domain-model.md`. Write these once there's an actual image to containerize; a compose file with no buildable service behind it isn't useful and risks drifting from what actually gets built.
