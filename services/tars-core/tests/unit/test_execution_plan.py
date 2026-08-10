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


def test_plan_round_trips_through_json_without_losing_warnings() -> None:
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
    plan = ExecutionPlan(
        query=_query(),
        connection_id="conn-1",
        root=root,
        is_actual=True,
        captured_at=datetime.now(UTC),
    )

    restored = ExecutionPlan.model_validate_json(plan.model_dump_json())

    assert restored.root.warnings[0].kind is PlanWarningKind.ROW_ESTIMATE_MISMATCH
    assert restored.root.warnings[0].severity is Severity.CRITICAL
    assert restored.root.actual_rows == 95_000
