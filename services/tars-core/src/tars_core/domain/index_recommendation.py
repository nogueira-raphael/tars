"""IndexRecommendation value object.

Recommendation-only by design — no apply path (see docs/architecture/
overview.md and the approval-gate scope note in
docs/adr/0006-approval-gate-via-mcp-elicitation.md).

Plain stdlib `dataclasses`, not Pydantic — see
docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tars_core.domain.severity import Severity


class IndexRecommendationKind(StrEnum):
    MISSING = "missing"
    """A new index would likely help — no matching index exists today."""
    UNUSED = "unused"
    """An existing index is never (or rarely) used by the query planner."""
    REDUNDANT = "redundant"
    """An existing index is a strict subset/prefix of another and adds no value."""


@dataclass(frozen=True, slots=True)
class IndexRecommendation:
    kind: IndexRecommendationKind
    severity: Severity
    schema_name: str
    table: str
    columns: list[str]
    """For MISSING: the suggested index's columns. For UNUSED/REDUNDANT: the
    existing index's columns."""
    rationale: str
    existing_index_name: str | None = None
    """Set for UNUSED/REDUNDANT; None for MISSING."""
    estimated_benefit: str | None = None
    """Free-text estimate (e.g. "could avoid a sequential scan reading ~2M
    rows"), not a formal cost number — the underlying analysis differs too
    much between engines to normalize into a single unit here."""
