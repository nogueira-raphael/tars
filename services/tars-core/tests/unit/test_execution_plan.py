import dataclasses
import json
from datetime import UTC, datetime

from tars_core.domain.connection import Engine
from tars_core.domain.execution_plan import (
    ExecutionPlan,
    PlanNode,
    PlanOperation,
    PlanWarning,
    PlanWarningKind,
)
from tars_core.domain.query import Query
from tars_core.domain.severity import Severity


def _query() -> Query:
    return Query(
        sql="SELECT * FROM film f JOIN actor a ON a.id = f.actor_id", engine=Engine.POSTGRESQL
    )


def test_plan_node_tree_holds_children_in_order() -> None:
    scan_film = PlanNode(
        node_id="1", operation=PlanOperation.SEQUENTIAL_SCAN, raw_operation_name="Seq Scan"
    )
    scan_actor = PlanNode(
        node_id="2", operation=PlanOperation.INDEX_SCAN, raw_operation_name="Index Scan"
    )
    join = PlanNode(
        node_id="0",
        operation=PlanOperation.HASH_JOIN,
        raw_operation_name="Hash Join",
        children=[scan_film, scan_actor],
    )

    assert [child.node_id for child in join.children] == ["1", "2"]


def test_unmapped_operator_falls_back_to_other_without_losing_the_raw_name() -> None:
    node = PlanNode(
        node_id="0", operation=PlanOperation.OTHER, raw_operation_name="Columnstore Index Scan"
    )

    assert node.operation is PlanOperation.OTHER
    assert node.raw_operation_name == "Columnstore Index Scan"


def test_estimate_only_plan_has_no_actual_stats() -> None:
    root = PlanNode(
        node_id="0", operation=PlanOperation.SEQUENTIAL_SCAN, raw_operation_name="Seq Scan"
    )
    plan = ExecutionPlan(
        query=_query(),
        connection_id="conn-1",
        root=root,
        is_actual=False,
        captured_at=datetime.now(UTC),
    )

    assert plan.is_actual is False
    assert plan.root.actual_rows is None
    assert plan.execution_time_ms is None


def _plan_with_a_warning() -> ExecutionPlan:
    root = PlanNode(
        node_id="0",
        operation=PlanOperation.SEQUENTIAL_SCAN,
        raw_operation_name="Seq Scan",
        target_relation="film",
        estimated_rows=100,
        actual_rows=95_000,
        warnings=[
            PlanWarning(
                kind=PlanWarningKind.ROW_ESTIMATE_MISMATCH,
                severity=Severity.CRITICAL,
                message="estimated 100 rows, actual 95000",
            )
        ],
    )
    return ExecutionPlan(
        query=_query(),
        connection_id="conn-1",
        root=root,
        is_actual=True,
        captured_at=datetime(2026, 8, 10, tzinfo=UTC),
    )


def test_dataclasses_give_value_equality_for_free() -> None:
    # Two independently-built trees with identical data are equal — the
    # property Cosmic Python calls out as the point of using dataclasses for
    # value objects/entities instead of a validation-library base class.
    assert _plan_with_a_warning() == _plan_with_a_warning()


def test_plan_is_serializable_with_stdlib_alone_no_pydantic_required() -> None:
    # Domain objects stay dependency-free (see docs/adr/0012); this only
    # proves `dataclasses.asdict` + stdlib `json` can turn one into a plain
    # dict, not that this is the final MCP-boundary wire format — that
    # belongs to mcp-server's infrastructure layer, not here.
    plan = _plan_with_a_warning()

    as_dict = dataclasses.asdict(plan)
    raw = json.dumps(as_dict, default=str)
    restored = json.loads(raw)

    assert restored["root"]["warnings"][0]["kind"] == PlanWarningKind.ROW_ESTIMATE_MISMATCH.value
    assert restored["root"]["warnings"][0]["severity"] == Severity.CRITICAL.value
    assert restored["root"]["actual_rows"] == 95_000
