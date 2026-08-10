# 11. MIT license

**Status:** Accepted — 2026-08-07

## Context

TARS is open-source-first by principle. A license needs to be picked before the repository is public. Apache 2.0 was considered as an alternative, for its explicit patent grant — relevant for infrastructure/dev-tooling projects that enterprises may embed, and the license used by some of the closest philosophical peers surveyed in the competitive landscape research (Google's MCP Toolbox, DBeaver, the core of Wren AI).

## Decision

MIT.

## Rationale

Simplicity and maximal permissiveness were prioritized over the patent grant. This also deliberately avoids the source-available/dual-license pattern seen in some adjacent tools (Bytebase, Chat2DB), which mix an open core with proprietary enterprise-gated code — a model TARS's "Open Source First" principle explicitly wants to avoid resembling even partially.

## Consequences

- No explicit patent grant to contributors/users — a theoretical gap in a world where that increasingly matters for enterprise adoption of infrastructure tooling, accepted as a trade-off for simplicity.
- Every file, dependency choice, and generated artifact should stay MIT-compatible; anything under Apache 2.0 or a permissive-but-not-MIT-compatible license needs a second look before being added as a dependency baked into a distributed artifact (not a concern for typical dev dependencies).
