# Contributing to TARS

Thanks for taking a look. The project is early — architecture is settled (`docs/architecture/`, `docs/adr/`), implementation is just starting, so this document will grow as real workflows exist.

## Before you open a PR

1. Read `docs/architecture/overview.md` and, if your change touches something with an ADR, read that ADR first. If you disagree with a past decision, open an issue proposing a new ADR that supersedes it rather than quietly diverging in code.
2. Know which bounded context your change belongs to — Diagnostics (`tars-core`), the MCP protocol adapter (`mcp-server`), or Conversation (`orchestrator`). See `docs/architecture/domain-model.md`.
3. Respect the dependency rules in `AGENTS.md` — `domain/` never depends on `application/`/`infrastructure/`, `orchestrator` never imports `tars-core` directly.

## Style

`STYLE_GUIDE.md`. In short: Google's Python and TypeScript style guides as the base; `ruff` + `mypy` (Python) and `biome` (TypeScript) enforce what's mechanical, the style guide covers the rest. Run the linters before pushing — CI will fail otherwise.

## Tests

- `tars-core`: unit tests against fake providers (no real database needed), integration tests against the demo containers (`docker/docker-compose.demo.yml`) for anything that talks to Postgres or SQL Server for real.
- New code needs tests. A PR that only adds implementation without tests will get a request for tests, not a merge.

## Commit / PR conventions

- Small, focused PRs over large ones — easier to review, easier to revert.
- Conventional commit-style prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`) are encouraged but not yet enforced by tooling.
- CI is split one pipeline per project (`.github/workflows/{tars-core,mcp-server,orchestrator,web}-ci.yml`), each path-triggered so touching one project doesn't run the others' checks — a PR that only touches `services/orchestrator` won't wait on `tars-core`'s pipeline. `mcp-server`'s pipeline also runs on `tars-core` changes, since it imports it directly. Every pipeline runs lint + type-check + tests on every push/PR; Docker images and the Tauri installer only build on release tags (not set up yet).

## Reporting bugs / proposing features

Open a GitHub issue. For anything that changes architecture (a new bounded context, a new dependency direction, a new external service), propose it as an ADR (`docs/adr/`, follow the format of an existing one) rather than just a code change.
