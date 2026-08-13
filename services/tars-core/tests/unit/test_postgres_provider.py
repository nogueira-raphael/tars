"""Unit tests for the pure, no-I/O helpers in `PostgresProvider` — JSON plan
translation, foreign-key grouping, and index-health heuristics. These take
plain data structures in and domain objects out, so they're tested without
a real Postgres connection.

Fixture shapes (the EXPLAIN JSON in particular) are taken from what a real
`postgres:17` container actually returns, not guessed — see the commit that
introduced `postgres.py` for how that was verified.
"""

from typing import Any

from tars_core.domain.execution_plan import PlanNode, PlanOperation
from tars_core.domain.index_recommendation import IndexRecommendationKind
from tars_core.infrastructure.providers.postgres import (
    _Counter,
    _group_foreign_keys,
    _parse_plan_node,
    _redundant_index_recommendations,
    _unused_index_recommendations,
)

# A real `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` "Plan" object: a hash
# join of two sequential scans. Typed `Any` — it's a deliberately
# heterogeneous JSON fixture, not a shape worth a TypedDict for.
_HASH_JOIN_PLAN: dict[str, Any] = {
    "Node Type": "Hash Join",
    "Join Type": "Inner",
    "Startup Cost": 17.25,
    "Total Cost": 122.35,
    "Plan Rows": 4003,
    "Plan Width": 34,
    "Actual Startup Time": 0.106,
    "Actual Total Time": 1.021,
    "Actual Rows": 4008,
    "Actual Loops": 1,
    "Hash Cond": "(o.customer_id = c.id)",
    "Shared Hit Blocks": 38,
    "Plans": [
        {
            "Node Type": "Seq Scan",
            "Relation Name": "orders",
            "Alias": "o",
            "Startup Cost": 0.0,
            "Total Cost": 94.5,
            "Plan Rows": 4003,
            "Plan Width": 22,
            "Actual Startup Time": 0.006,
            "Actual Total Time": 0.491,
            "Actual Rows": 4008,
            "Actual Loops": 1,
            "Filter": "(total > '100'::numeric)",
            "Rows Removed by Filter": 992,
        },
        {
            "Node Type": "Hash",
            "Startup Cost": 11.0,
            "Total Cost": 11.0,
            "Plan Rows": 500,
            "Plan Width": 16,
            "Actual Startup Time": 0.088,
            "Actual Total Time": 0.088,
            "Actual Rows": 500,
            "Actual Loops": 1,
            "Plans": [
                {
                    "Node Type": "Seq Scan",
                    "Relation Name": "customers",
                    "Alias": "c",
                    "Startup Cost": 0.0,
                    "Total Cost": 11.0,
                    "Plan Rows": 500,
                    "Plan Width": 16,
                    "Actual Startup Time": 0.002,
                    "Actual Total Time": 0.031,
                    "Actual Rows": 500,
                    "Actual Loops": 1,
                }
            ],
        },
    ],
}

# A real bitmap index scan tree: Bitmap Heap Scan over Bitmap Index Scan.
_BITMAP_SCAN_PLAN = {
    "Node Type": "Bitmap Heap Scan",
    "Relation Name": "orders",
    "Alias": "orders",
    "Startup Cost": 4.35,
    "Total Cost": 24.46,
    "Plan Rows": 9,
    "Actual Rows": 10,
    "Actual Loops": 1,
    "Recheck Cond": "(customer_id = 5)",
    "Plans": [
        {
            "Node Type": "Bitmap Index Scan",
            "Index Name": "idx_orders_customer_id",
            "Startup Cost": 0.0,
            "Total Cost": 4.35,
            "Plan Rows": 9,
            "Actual Rows": 10,
            "Actual Loops": 1,
            "Index Cond": "(customer_id = 5)",
        }
    ],
}


def test_parses_node_type_operation_and_cost_fields() -> None:
    node = _parse_plan_node(_HASH_JOIN_PLAN, _Counter())

    assert node.operation is PlanOperation.HASH_JOIN
    assert node.raw_operation_name == "Hash Join"
    assert node.estimated_total_cost == 122.35
    assert node.actual_rows == 4008
    assert node.join_condition == "(o.customer_id = c.id)"


def test_children_are_parsed_recursively_in_order() -> None:
    node = _parse_plan_node(_HASH_JOIN_PLAN, _Counter())

    assert [c.raw_operation_name for c in node.children] == ["Seq Scan", "Hash"]
    assert node.children[1].children[0].raw_operation_name == "Seq Scan"


def test_node_ids_are_unique_across_the_whole_tree() -> None:
    node = _parse_plan_node(_HASH_JOIN_PLAN, _Counter())

    def collect_ids(n: PlanNode) -> list[str]:
        ids = [n.node_id]
        for child in n.children:
            ids.extend(collect_ids(child))
        return ids

    ids = collect_ids(node)
    assert len(ids) == len(set(ids))


def test_seq_scan_captures_table_alias_and_filter() -> None:
    seq_scan = _HASH_JOIN_PLAN["Plans"][0]
    node = _parse_plan_node(seq_scan, _Counter())

    assert node.operation is PlanOperation.SEQUENTIAL_SCAN
    assert node.target_relation == "orders"
    assert node.alias == "o"
    assert node.filter == "(total > '100'::numeric)"


def test_unmapped_node_type_falls_back_to_other_without_losing_the_raw_name() -> None:
    node = _parse_plan_node({"Node Type": "WindowAgg", "Plan Rows": 1}, _Counter())

    assert node.operation is PlanOperation.OTHER
    assert node.raw_operation_name == "WindowAgg"


def test_bitmap_index_scan_captures_the_index_name_separately_from_the_table() -> None:
    node = _parse_plan_node(_BITMAP_SCAN_PLAN, _Counter())
    index_scan = node.children[0]

    assert node.target_relation == "orders"
    assert node.index_name is None  # Bitmap Heap Scan itself doesn't name an index.
    assert index_scan.index_name == "idx_orders_customer_id"
    assert index_scan.filter == "(customer_id = 5)"  # falls back to Index Cond.


def test_estimate_only_node_has_no_actual_fields() -> None:
    node = _parse_plan_node(
        {"Node Type": "Seq Scan", "Relation Name": "t", "Plan Rows": 10, "Total Cost": 1.0},
        _Counter(),
    )

    assert node.actual_rows is None
    assert node.actual_time_ms is None


def test_group_foreign_keys_builds_one_entry_per_constraint() -> None:
    rows = [
        {
            "table_name": "orders",
            "constraint_name": "orders_customer_id_fkey",
            "column_name": "customer_id",
            "foreign_schema": "store",
            "foreign_table": "customers",
            "foreign_column": "id",
        }
    ]

    grouped = _group_foreign_keys(rows)

    assert len(grouped["orders"]) == 1
    fk = grouped["orders"][0]
    assert fk.name == "orders_customer_id_fkey"
    assert fk.columns == ["customer_id"]
    assert fk.references_table == "customers"


def test_group_foreign_keys_handles_composite_keys() -> None:
    # A two-column foreign key comes back as two rows sharing a constraint name.
    rows = [
        {
            "table_name": "shipments",
            "constraint_name": "shipments_order_fkey",
            "column_name": "order_id",
            "foreign_schema": "store",
            "foreign_table": "order_items",
            "foreign_column": "order_id",
        },
        {
            "table_name": "shipments",
            "constraint_name": "shipments_order_fkey",
            "column_name": "line_no",
            "foreign_schema": "store",
            "foreign_table": "order_items",
            "foreign_column": "line_no",
        },
    ]

    grouped = _group_foreign_keys(rows)

    assert len(grouped["shipments"]) == 1
    fk = grouped["shipments"][0]
    assert fk.columns == ["order_id", "line_no"]
    assert fk.references_columns == ["order_id", "line_no"]


def _index_row(
    table: str,
    index: str,
    columns: list[str],
    idx_scan: int,
    pk: bool = False,
    unique: bool = False,
) -> dict[str, object]:
    return {
        "table_name": table,
        "index_name": index,
        "indisprimary": pk,
        "indisunique": unique,
        "columns": columns,
        "idx_scan": idx_scan,
    }


def test_unused_index_is_flagged() -> None:
    rows = [_index_row("orders", "idx_total_unused", ["total"], idx_scan=0)]

    recs = _unused_index_recommendations("store", rows)

    assert len(recs) == 1
    assert recs[0].kind is IndexRecommendationKind.UNUSED
    assert recs[0].existing_index_name == "idx_total_unused"


def test_used_index_is_not_flagged_as_unused() -> None:
    rows = [_index_row("orders", "idx_customer_id", ["customer_id"], idx_scan=42)]

    assert _unused_index_recommendations("store", rows) == []


def test_unused_primary_key_index_is_not_flagged() -> None:
    rows = [_index_row("orders", "orders_pkey", ["id"], idx_scan=0, pk=True)]

    assert _unused_index_recommendations("store", rows) == []


def test_unused_unique_index_is_not_flagged() -> None:
    rows = [_index_row("customers", "customers_email_key", ["email"], idx_scan=0, unique=True)]

    assert _unused_index_recommendations("store", rows) == []


def test_strict_prefix_index_is_flagged_as_redundant() -> None:
    rows = [
        _index_row("orders", "idx_customer_id", ["customer_id"], idx_scan=5),
        _index_row("orders", "idx_customer_id_total", ["customer_id", "total"], idx_scan=10),
    ]

    recs = _redundant_index_recommendations("store", rows)

    assert len(recs) == 1
    assert recs[0].existing_index_name == "idx_customer_id"
    assert "idx_customer_id_total" in recs[0].rationale


def test_non_prefix_indexes_on_different_columns_are_not_flagged() -> None:
    rows = [
        _index_row("orders", "idx_customer_id", ["customer_id"], idx_scan=5),
        _index_row("orders", "idx_total", ["total"], idx_scan=10),
    ]

    assert _redundant_index_recommendations("store", rows) == []


def test_exact_duplicate_indexes_are_flagged_only_once() -> None:
    rows = [
        _index_row("orders", "idx_a_customer_id", ["customer_id"], idx_scan=5),
        _index_row("orders", "idx_b_customer_id", ["customer_id"], idx_scan=5),
    ]

    recs = _redundant_index_recommendations("store", rows)

    # Only the alphabetically-later one is reported, not both directions.
    assert len(recs) == 1
    assert recs[0].existing_index_name == "idx_b_customer_id"
