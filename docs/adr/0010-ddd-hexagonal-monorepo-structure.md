# 10. Monorepo, Hexagonal/DDD structure, applied strongly only where domain complexity is real

**Status:** Accepted — 2026-08-10

## Context

The project has three Python services (sharing a domain of database diagnostics and conversation/session management) and one TypeScript web app. It needs a repository layout and an internal architecture style before real code gets written, and the team wants to "follow DDD strongly."

## Decision

A single monorepo (`services/*` in one `uv` workspace, plus `web/`). Internally, Hexagonal/Ports & Adapters as the pairing for DDD tactical patterns — but applied **strongly only in `tars-core` and `orchestrator`**, where real domain complexity exists (diagnostic normalization, index analysis, session/approval state). `mcp-server` is deliberately kept thin, with no domain layer of its own — it's a protocol adapter, not a place with business rules to protect. Full layout: `docs/architecture/domain-model.md`.

Dependency rule: `domain/` never imports `application/` or `infrastructure/`; `application/` only depends on `domain/ports.py` interfaces, never a concrete adapter. `orchestrator` never imports `tars-core` directly — it only reaches diagnostics functionality through an MCP tool call, via `mcp-server`.

Also decided in the same pass: `mypy` (strict) for type-checking (not `pyright`); build order `tars-core` → `mcp-server` → SQL Server provider → `orchestrator` → `web`; a single version number for the whole repo, not independent per-package versions; CI runs lint+test on every push/PR, and builds/publishes Docker images + the Tauri installer only on release tags.

## Rationale

DDD/Hexagonal is a good fit where there's real domain complexity worth protecting from infrastructure churn — `tars-core`'s diagnostic model and `orchestrator`'s session/approval state machine both qualify. Applying the same ceremony to `mcp-server`, which is intentionally a thin, deterministic translation layer (see `docs/adr/0006-...` and the "AI optional" principle), would be over-engineering: there's no domain logic there to protect, only protocol wiring. A single monorepo (over multiple repos) was chosen because there's no external ecosystem yet consuming any one service independently — one CI pipeline and one place to file issues/PRs is simpler for an early-stage open-source project than coordinating versions across repos.

## Consequences

- `tars-core`'s unit tests can run with zero real database — they swap `DatabaseProvider` for a fake, per the dependency rule.
- Adding a capability requires first identifying which bounded context (Diagnostics/`tars-core` vs. Conversation/`orchestrator`) it belongs to before deciding where the code goes.
- The `web/` frontend mirrors this thinking with feature-sliced (not layer-sliced) organization — see `docs/architecture/domain-model.md`.
- If `tars-core` is ever published as a standalone PyPI package for reuse outside this monorepo, this decision (single repo, single version) would need revisiting — not expected soon.
