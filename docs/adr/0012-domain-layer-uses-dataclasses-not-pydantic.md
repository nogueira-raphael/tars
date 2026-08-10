# 12. Domain layer uses stdlib `dataclasses`, not Pydantic

**Status:** Accepted — 2026-08-10

## Context

`tars-core`'s and `orchestrator`'s domain models (`ExecutionPlan`, `SchemaGraph`, `LockTree`, `ChatSession`, etc.) were first implemented using Pydantic `BaseModel`, since Pydantic v2 is already a dependency for validation elsewhere in the stack (see `docs/architecture/tech-stack.md`). This directly contradicted a rule stated in `AGENTS.md` and `docs/adr/0010-ddd-hexagonal-monorepo-structure.md` from the start: `domain/` should have zero dependency on any framework or library.

## Decision

Domain entities, value objects, and aggregates use plain stdlib `dataclasses` (`@dataclass(frozen=True, slots=True)` for value objects, `@dataclass(slots=True)` for entities/aggregates) — no Pydantic import anywhere under `domain/`, in either `tars-core` or `orchestrator`. `tars-core`'s `pydantic` dependency was removed entirely from its `pyproject.toml`, since nothing in that package needs it anymore.

Pydantic stays exactly where it already belonged: at infrastructure/interface boundaries — `mcp-server`'s future tool-argument validation (parsing untrusted MCP input into domain objects) and `orchestrator`'s future FastAPI request/response models (`infrastructure/api/`). `orchestrator` keeps `pydantic` as a dependency for that reason; `tars-core` does not, because no boundary code needing it exists in that package.

## Rationale

This is a well-documented, currently active debate in the Python community (mid-2026), and the pattern that keeps recurring across sources — Cosmic Python (the reference text for this exact architecture style), multiple hexagonal-architecture writeups, and Pydantic's own maintainers — is the same one: **Pydantic at the edge, dataclasses at the core**. Concretely:

- Coupling the domain to Pydantic means the domain can't be imported, tested, or reasoned about without a third-party validation library installed — exactly the dependency direction Hexagonal/DDD is supposed to prevent (`docs/adr/0010`).
- Pydantic's declarative field validation encourages checking *shape* (types, constraints) at construction time and calling that "done," which tends to produce an anemic domain model — entities that are bags of validated fields with no real behavior — rather than encoding actual business invariants as methods on the entity itself.
- Pydantic model instantiation carries measurable validation overhead per object versus a plain dataclass — relevant here because `PlanNode` trees can be large and get built repeatedly per `explain_query` call.
- Validating untrusted external input (an MCP tool call's raw arguments, a FastAPI request body) is a genuinely different job from modeling the domain, and Pydantic is excellent at the former — the fix isn't "stop using Pydantic," it's "stop using it in the wrong layer."

## Consequences

- `tars-core/pyproject.toml` no longer lists `pydantic` as a dependency at all.
- Parsing raw engine output (Postgres `EXPLAIN` JSON, SQL Server showplan XML) into domain dataclasses, and serializing domain dataclasses back out over MCP, are explicitly infrastructure/interface concerns — not yet built, and when they are, that's where a Pydantic (or hand-rolled) DTO layer with `to_domain()`/`from_domain()`-style mapping belongs, not inside `domain/`.
- Domain unit tests can no longer rely on `.model_dump_json()`/`.model_validate_json()`; they use `dataclasses.asdict()` + stdlib `json` where JSON-shape testing is useful, and plain equality (`dataclasses` gives `__eq__` for free) otherwise.
- This is a second instance of the same mistake being caught (it was first introduced in the initial scaffold's `orchestrator.domain.message.Message`/`chat_session.ChatSession` placeholders too, fixed in the same pass) — worth double-checking any future domain addition doesn't reach for Pydantic out of habit.
