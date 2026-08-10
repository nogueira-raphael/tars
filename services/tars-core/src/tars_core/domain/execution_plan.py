"""ExecutionPlan aggregate — the normalized execution-plan schema.

Design basis (see docs/adr/0007-normalized-diagnostic-schema.md): PostgreSQL's
`EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` output (a tree of nodes with fields
like `Node Type`, `Total Cost`, `Plan Rows`, `Actual Rows`, `Actual Loops`)
and SQL Server's showplan XML (`StmtSimple/QueryPlan/RelOp`, with
`PhysicalOp`/`LogicalOp`, `EstimateRows`, `EstimatedTotalSubtreeCost`, and
`RunTimeCountersPerThread/ActualRows` when captured with actual execution
stats).

Both engines expose the same underlying shape — a tree of operators, each
with an estimated cost/row count and, optionally, actual runtime stats — but
disagree on vocabulary, on how granular the operator taxonomy is, and on
which fields exist at all (Postgres exposes per-node startup cost; SQL
Server doesn't). `PlanNode.operation` normalizes the taxonomy with a
best-effort mapping; `PlanNode.raw_operation_name` and
`PlanNode.engine_specific` preserve what doesn't map cleanly, so nothing is
silently lost for the sake of forcing a false equivalence.

Plain stdlib `dataclasses`, not Pydantic — see
docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md. Parsing raw
EXPLAIN/showplan output into these types, and serializing them back out over
MCP, are infrastructure/interface concerns, not domain ones — that's where
Pydantic (or a hand-rolled JSON encoder) belongs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from tars_core.domain.query import Query
from tars_core.domain.severity import Severity


class PlanOperation(StrEnum):
    """Normalized operator taxonomy. `OTHER` is the deliberate escape hatch —
    this enum is not expected to ever be exhaustive across engines; anything
    that doesn't map cleanly stays `OTHER` with the real name preserved in
    `PlanNode.raw_operation_name`.
    """

    SEQUENTIAL_SCAN = "sequential_scan"
    INDEX_SCAN = "index_scan"
    INDEX_ONLY_SCAN = "index_only_scan"
    BITMAP_SCAN = "bitmap_scan"
    HASH_JOIN = "hash_join"
    MERGE_JOIN = "merge_join"
    NESTED_LOOP_JOIN = "nested_loop_join"
    SORT = "sort"
    AGGREGATE = "aggregate"
    HASH_AGGREGATE = "hash_aggregate"
    LIMIT = "limit"
    FILTER = "filter"
    MATERIALIZE = "materialize"
    APPEND = "append"
    UNIQUE = "unique"
    PARALLEL_GATHER = "parallel_gather"
    OTHER = "other"


class PlanWarningKind(StrEnum):
    ROW_ESTIMATE_MISMATCH = "row_estimate_mismatch"
    MISSING_INDEX = "missing_index"
    IMPLICIT_CONVERSION = "implicit_conversion"
    SPILL_TO_DISK = "spill_to_disk"
    SEQUENTIAL_SCAN_ON_LARGE_RELATION = "sequential_scan_on_large_relation"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class PlanWarning:
    kind: PlanWarningKind
    severity: Severity
    message: str


@dataclass(slots=True)
class PlanNode:
    """One operator in the plan tree. Costs and times are only meaningful
    *within* a single plan — never compare `estimated_total_cost` or
    `actual_time_ms` across two plans from different engines, their units
    aren't the same currency.
    """

    node_id: str
    operation: PlanOperation
    raw_operation_name: str
    """The engine-native operator name (e.g. "Hash Join" or "Hash Match") —
    always populated, even when `operation` is a specific (non-OTHER) value."""

    target_schema: str | None = None
    target_relation: str | None = None
    """Table or index name this node reads from, if any."""
    alias: str | None = None

    estimated_rows: float | None = None
    actual_rows: float | None = None
    """None when this plan is estimate-only (no ANALYZE / actual execution)."""

    estimated_startup_cost: float | None = None
    """Postgres-only concept in practice — SQL Server doesn't expose an
    equivalent per-operator startup cost."""
    estimated_total_cost: float | None = None

    actual_time_ms: float | None = None
    loop_count: int | None = None

    filter: str | None = None
    join_condition: str | None = None
    sort_keys: list[str] = field(default_factory=list)

    warnings: list[PlanWarning] = field(default_factory=list)
    children: list[PlanNode] = field(default_factory=list)

    engine_specific: dict[str, object] = field(default_factory=dict)
    """Raw passthrough for fields that don't normalize cleanly (e.g. Postgres's
    buffer hit/read counts, SQL Server's memory grant info). Not meant for the
    Web UI's default rendering — an escape hatch for engine-specific tooling
    or debugging, not a place to quietly duplicate the normalized fields above.
    """


@dataclass(slots=True)
class ExecutionPlan:
    """Aggregate root returned by `explain_query`."""

    query: Query
    connection_id: str
    root: PlanNode
    is_actual: bool
    """True if this plan carries real execution stats (ANALYZE); False if
    it's estimate-only. `actual_rows`/`actual_time_ms` are None throughout
    the tree when this is False."""
    captured_at: datetime
    planning_time_ms: float | None = None
    execution_time_ms: float | None = None
