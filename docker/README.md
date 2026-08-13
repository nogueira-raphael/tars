# docker

Two compose files, per `/docs/adr/0005-containerized-local-first-deployment.md`:

- `docker-compose.yml` — base: `mcp-server`, `orchestrator`, `web-ui`. Assumes the user already has databases to point at. Orchestrator's port must publish to `127.0.0.1` (not `0.0.0.0`) so a natively-installed Tauri app on the host can reach it.
- `docker-compose.demo.yml` — overlay adding a sample PostgreSQL ([Pagila](https://github.com/devrimgunduz/pagila), PostgreSQL License) and SQL Server ([AdventureWorksLT](https://github.com/microsoft/sql-server-samples), MIT) container, seeded automatically via container init scripts. No manual seed step. BIRD-bench was considered and rejected for this — 33GB, CC BY-SA 4.0 licensing friction against MIT, and it's a text-to-SQL benchmark, not a general demo dataset (the category TARS differentiates itself from).

**Not written yet.** Both files depend on services that don't exist yet (`mcp-server`, `orchestrator`, `web`) — see the build order in `/docs/architecture/domain-model.md`. Write these once there's an actual image to containerize; a compose file with no buildable service behind it isn't useful and risks drifting from what actually gets built.

**Idea, not decided/scheduled:** a small tool (script or `make` target — e.g. `scripts/load-demo-db.sh <name-or-path>`) to load a *different* sample or custom database into the running demo containers, for testing `tars-core` against schemas beyond Pagila/AdventureWorksLT during development. Worth having before relying too heavily on just these two fixed datasets to validate the normalized diagnostic schema (`docs/adr/0007-normalized-diagnostic-schema.md`) — but not needed to ship v1's demo experience, so not scoped further yet.
