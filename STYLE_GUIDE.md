# Style Guide

TARS doesn't maintain its own prose style guide from scratch. It adopts an established one per language and documents only where this project deviates. Linters enforce the mechanical parts (formatting, import order, obvious lint rules); this document is for the judgment calls linters don't make — naming semantics, comment discipline, module layout, API shape.

## Python (`services/*`)

Base: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

Enforced by tooling, not manual review: `ruff` (lint + format, config in the root `pyproject.toml`) and `mypy --strict` (type-checking). If `ruff` and the Google guide disagree on formatting specifics (line length, quote style), `ruff`'s defaults win — the goal is one obvious answer per question, not two authorities to reconcile.

Deviations from the Google guide:
- **Type hints are mandatory everywhere**, including internal functions. Google's guide treats them as encouraged; here they're required (`mypy --strict` enforces this in CI).
- **No `# type: ignore` without a linked issue.** If `mypy --strict` is wrong about something, comment why and link where it's tracked, don't just silence it.
- **`domain/` modules import nothing from `application/` or `infrastructure/`, ever** — this is a project-specific architectural rule on top of the style guide, not a Google convention. See `AGENTS.md` and `docs/architecture/domain-model.md`.
- Docstrings: Google-style docstrings (as the guide already prescribes) on every public class and function in `domain/` and `application/`. Infrastructure adapters get a docstring only where the "why this implementation" isn't obvious from the port it implements.

## TypeScript (`web/`)

Base: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html).

Enforced by tooling: `biome check` (lint + format, replaces ESLint + Prettier — config in `web/biome.json` once it exists). Same rule as Python: where Biome's formatting defaults and the Google guide disagree on formatting mechanics, Biome wins.

Deviations from the Google guide:
- **Functional components + hooks only.** The Google guide predates modern React conventions and doesn't take a strong position here; this project has one: no class components.
- **Feature-sliced structure**, not layer-sliced. Google's guide is language-level and doesn't prescribe project layout; TARS organizes `web/src/` by feature (`features/chat/`, `features/plan-viewer/`, ...), not by technical type (`components/`, `hooks/` at the top level). See `docs/architecture/domain-model.md`.
- **No default exports** for anything except route/page-level components, to keep refactors and grep-ability sane — a common deviation from the Google guide's silence on the topic.

## Both languages

- Comments explain *why*, not *what* — the code should already say what it does. See the project's general engineering conventions in `AGENTS.md`.
- No commented-out code in commits. Delete it; git history has it if it's ever needed back.
