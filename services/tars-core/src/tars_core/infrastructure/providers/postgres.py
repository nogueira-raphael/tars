"""PostgreSQL implementation of `DatabaseProvider`, via `psycopg3` (async).

Built first — see docs/architecture/domain-model.md's build order. Every
query here was verified against a real `postgres:17` container before being
written, not guessed from documentation — see the empirical notes below on
the few places Postgres's behavior isn't obvious from the catalog docs
alone.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from tars_core.domain.connection import Connection
from tars_core.domain.execution_plan import ExecutionPlan, PlanNode, PlanOperation
from tars_core.domain.index_recommendation import IndexRecommendation, IndexRecommendationKind
from tars_core.domain.locks import BlockingSession, LockTree, SessionState
from tars_core.domain.ports import ConnectionRepository
from tars_core.domain.query import Query
from tars_core.domain.schema_graph import Column, ForeignKey, SchemaGraph, Table
from tars_core.domain.severity import Severity

_OPERATION_BY_NODE_TYPE = {
    "Seq Scan": PlanOperation.SEQUENTIAL_SCAN,
    "Index Scan": PlanOperation.INDEX_SCAN,
    "Index Only Scan": PlanOperation.INDEX_ONLY_SCAN,
    "Bitmap Heap Scan": PlanOperation.BITMAP_SCAN,
    "Bitmap Index Scan": PlanOperation.BITMAP_SCAN,
    "Hash Join": PlanOperation.HASH_JOIN,
    "Merge Join": PlanOperation.MERGE_JOIN,
    "Nested Loop": PlanOperation.NESTED_LOOP_JOIN,
    "Sort": PlanOperation.SORT,
    "Aggregate": PlanOperation.AGGREGATE,
    "HashAggregate": PlanOperation.HASH_AGGREGATE,
    "Limit": PlanOperation.LIMIT,
    "Materialize": PlanOperation.MATERIALIZE,
    "Append": PlanOperation.APPEND,
    "Unique": PlanOperation.UNIQUE,
    "Gather": PlanOperation.PARALLEL_GATHER,
    "Gather Merge": PlanOperation.PARALLEL_GATHER,
}
"""Not exhaustive on purpose — see docs/adr/0007-normalized-diagnostic-schema.md.
Anything not listed here stays `PlanOperation.OTHER`, with the real Postgres
node type preserved in `PlanNode.raw_operation_name`."""

_SESSION_STATE_BY_PG_STATE = {
    "active": SessionState.ACTIVE,
    "idle": SessionState.IDLE,
    "idle in transaction": SessionState.IDLE_IN_TRANSACTION,
    "idle in transaction (aborted)": SessionState.IDLE_IN_TRANSACTION,
}

# Fields carried straight through into PlanNode.engine_specific — buffer and
# parallel-execution detail that doesn't have a normalized home, but is
# still worth keeping for anyone inspecting a raw plan.
_PASSTHROUGH_NODE_FIELDS = (
    "Shared Hit Blocks",
    "Shared Read Blocks",
    "Shared Dirtied Blocks",
    "Shared Written Blocks",
    "Temp Read Blocks",
    "Temp Written Blocks",
    "Rows Removed by Filter",
    "Workers Planned",
    "Workers Launched",
)


class PostgresProvider:
    """See `tars_core.domain.ports.DatabaseProvider` for the contract.

    Needs the same `ConnectionRepository` the MCP Server's connection
    registry uses, to resolve a `Connection.credential_ref` into the
    plaintext password immediately before opening each connection — never
    stored, logged, or held longer than the `psycopg` connect call needs it.
    """

    def __init__(self, connection_repository: ConnectionRepository) -> None:
        self._connection_repository = connection_repository

    async def _connect(self, connection: Connection) -> psycopg.AsyncConnection[dict[str, Any]]:
        password = await self._connection_repository.resolve_credential(connection.credential_ref)
        return await psycopg.AsyncConnection.connect(
            host=connection.host,
            port=connection.port,
            dbname=connection.database,
            user=connection.username,
            password=password,
            row_factory=dict_row,
        )

    async def list_schemas(self, connection: Connection) -> list[str]:
        async with await self._connect(connection) as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                  AND schema_name NOT LIKE 'pg\\_toast%'
                  AND schema_name NOT LIKE 'pg\\_temp%'
                ORDER BY schema_name
                """
            )
            rows = await cur.fetchall()
        return [row["schema_name"] for row in rows]

    async def list_tables(self, connection: Connection, schema: str) -> SchemaGraph:
        async with await self._connect(connection) as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = %s ORDER BY tablename",
                (schema,),
            )
            table_names = [row["tablename"] for row in await cur.fetchall()]

            await cur.execute(
                """
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
                """,
                (schema,),
            )
            column_rows = await cur.fetchall()

            await cur.execute(
                """
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = %s AND tc.constraint_type = 'PRIMARY KEY'
                """,
                (schema,),
            )
            pk_columns: dict[str, set[str]] = {}
            for row in await cur.fetchall():
                pk_columns.setdefault(row["table_name"], set()).add(row["column_name"])

            await cur.execute(
                """
                SELECT tc.table_name, tc.constraint_name, kcu.column_name,
                       ccu.table_schema AS foreign_schema, ccu.table_name AS foreign_table,
                       ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s
                ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position
                """,
                (schema,),
            )
            fk_rows = await cur.fetchall()

            await cur.execute(
                """
                SELECT c.relname AS table_name, c.reltuples::bigint AS estimate,
                       pg_total_relation_size(c.oid) AS size_bytes
                FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = %s AND c.relkind = 'r'
                """,
                (schema,),
            )
            stats_by_table = {row["table_name"]: row for row in await cur.fetchall()}

        columns_by_table: dict[str, list[Column]] = {}
        for row in column_rows:
            columns_by_table.setdefault(row["table_name"], []).append(
                Column(
                    name=row["column_name"],
                    raw_data_type=row["data_type"],
                    nullable=row["is_nullable"] == "YES",
                    default=row["column_default"],
                    is_primary_key=row["column_name"] in pk_columns.get(row["table_name"], set()),
                )
            )

        foreign_keys_by_table = _group_foreign_keys(fk_rows)

        tables = [
            Table(
                name=name,
                schema_name=schema,
                columns=columns_by_table.get(name, []),
                foreign_keys=foreign_keys_by_table.get(name, []),
                estimated_row_count=stats_by_table[name]["estimate"]
                if name in stats_by_table
                else None,
                size_bytes=stats_by_table[name]["size_bytes"] if name in stats_by_table else None,
            )
            for name in table_names
        ]
        return SchemaGraph(connection_id=str(connection.id), schema_name=schema, tables=tables)

    async def explain_query(
        self, connection: Connection, query: Query, *, analyze: bool
    ) -> ExecutionPlan:
        options = "ANALYZE, BUFFERS, FORMAT JSON" if analyze else "FORMAT JSON"
        async with await self._connect(connection) as conn, conn.cursor() as cur:
            await cur.execute(f"EXPLAIN ({options}) {query.sql}")
            row = await cur.fetchone()
        assert row is not None  # EXPLAIN always returns exactly one row.
        plan_json = row["QUERY PLAN"][0]

        return ExecutionPlan(
            query=query,
            connection_id=str(connection.id),
            root=_parse_plan_node(plan_json["Plan"], next_id=_Counter()),
            is_actual=analyze,
            captured_at=datetime.now(UTC),
            planning_time_ms=plan_json.get("Planning Time"),
            execution_time_ms=plan_json.get("Execution Time"),
        )

    async def index_health(self, connection: Connection, schema: str) -> list[IndexRecommendation]:
        async with await self._connect(connection) as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    t.relname AS table_name,
                    i.relname AS index_name,
                    ix.indisprimary,
                    ix.indisunique,
                    array_agg(a.attname ORDER BY k.ord) AS columns,
                    COALESCE(s.idx_scan, 0) AS idx_scan
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS k(attnum, ord) ON true
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
                LEFT JOIN pg_stat_user_indexes s ON s.indexrelid = ix.indexrelid
                WHERE n.nspname = %s
                GROUP BY t.relname, i.relname, ix.indisprimary, ix.indisunique, s.idx_scan
                ORDER BY t.relname, i.relname
                """,
                (schema,),
            )
            index_rows = await cur.fetchall()

        return _unused_index_recommendations(schema, index_rows) + _redundant_index_recommendations(
            schema, index_rows
        )

    async def active_sessions(self, connection: Connection) -> LockTree:
        async with await self._connect(connection) as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT pid, datname, state, wait_event_type, wait_event, query, query_start,
                       pg_blocking_pids(pid) AS blocked_by
                FROM pg_stat_activity
                WHERE pid <> pg_backend_pid() AND datname IS NOT NULL
                """
            )
            rows = await cur.fetchall()

        sessions = [
            BlockingSession(
                session_id=str(row["pid"]),
                state=_SESSION_STATE_BY_PG_STATE.get(row["state"], SessionState.OTHER),
                database=row["datname"],
                query_text=row["query"] or None,
                wait_type=row["wait_event"],
                lock_mode=None,  # not surfaced by pg_stat_activity alone; would need pg_locks.
                blocked_by=[str(pid) for pid in row["blocked_by"]],
                started_at=row["query_start"],
            )
            for row in rows
        ]
        return LockTree(
            connection_id=str(connection.id), sessions=sessions, captured_at=datetime.now(UTC)
        )

    async def execute_sql(self, connection: Connection, query: Query) -> object:
        # Return shape is provisional — the MCP-boundary contract for tool
        # results hasn't been designed yet (see docs/architecture/overview.md).
        async with await self._connect(connection) as conn, conn.cursor() as cur:
            await cur.execute(query.sql)
            if cur.description is None:
                return {"row_count": cur.rowcount}
            return {"rows": await cur.fetchall()}


class _Counter:
    """A tiny mutable counter for assigning stable node ids while walking
    the plan tree — plain int + nonlocal would work too, but this reads
    clearer at each recursive call site."""

    def __init__(self) -> None:
        self._value = 0

    def next(self) -> str:
        self._value += 1
        return str(self._value)


def _parse_plan_node(node: dict[str, Any], next_id: _Counter) -> PlanNode:
    node_type = node.get("Node Type", "")
    return PlanNode(
        node_id=next_id.next(),
        operation=_OPERATION_BY_NODE_TYPE.get(node_type, PlanOperation.OTHER),
        raw_operation_name=node_type,
        target_schema=None,  # Postgres's EXPLAIN JSON doesn't include the schema per node.
        target_relation=node.get("Relation Name"),
        index_name=node.get("Index Name"),
        alias=node.get("Alias"),
        estimated_rows=node.get("Plan Rows"),
        actual_rows=node.get("Actual Rows"),
        estimated_startup_cost=node.get("Startup Cost"),
        estimated_total_cost=node.get("Total Cost"),
        actual_time_ms=node.get("Actual Total Time"),
        loop_count=node.get("Actual Loops"),
        filter=node.get("Filter") or node.get("Index Cond") or node.get("Recheck Cond"),
        join_condition=node.get("Hash Cond") or node.get("Merge Cond"),
        sort_keys=node.get("Sort Key", []),
        children=[_parse_plan_node(child, next_id) for child in node.get("Plans", [])],
        engine_specific={key: node[key] for key in _PASSTHROUGH_NODE_FIELDS if key in node},
    )


def _group_foreign_keys(fk_rows: list[dict[str, Any]]) -> dict[str, list[ForeignKey]]:
    by_constraint: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in fk_rows:
        key = (row["table_name"], row["constraint_name"])
        by_constraint.setdefault(key, []).append(row)

    result: dict[str, list[ForeignKey]] = {}
    for (table_name, constraint_name), rows in by_constraint.items():
        first = rows[0]
        fk = ForeignKey(
            name=constraint_name,
            columns=[r["column_name"] for r in rows],
            references_schema=first["foreign_schema"],
            references_table=first["foreign_table"],
            references_columns=[r["foreign_column"] for r in rows],
        )
        result.setdefault(table_name, []).append(fk)
    return result


def _unused_index_recommendations(
    schema: str, index_rows: list[dict[str, Any]]
) -> list[IndexRecommendation]:
    return [
        IndexRecommendation(
            kind=IndexRecommendationKind.UNUSED,
            severity=Severity.INFO,
            schema_name=schema,
            table=row["table_name"],
            columns=list(row["columns"]),
            existing_index_name=row["index_name"],
            rationale=(
                "Never selected by the planner (0 scans) since its statistics were last reset."
            ),
        )
        for row in index_rows
        # A primary key or unique index enforces a constraint regardless of
        # scan count — dropping it isn't a pure performance decision, so it
        # doesn't belong in a "this index is dead weight" recommendation.
        if row["idx_scan"] == 0 and not row["indisprimary"] and not row["indisunique"]
    ]


def _redundant_index_recommendations(
    schema: str, index_rows: list[dict[str, Any]]
) -> list[IndexRecommendation]:
    by_table: dict[str, list[dict[str, Any]]] = {}
    for row in index_rows:
        by_table.setdefault(row["table_name"], []).append(row)

    recommendations = []
    for table_name, rows in by_table.items():
        for candidate in rows:
            candidate_columns = list(candidate["columns"])
            for other in rows:
                if other["index_name"] == candidate["index_name"]:
                    continue
                other_columns = list(other["columns"])

                is_strict_prefix = (
                    len(candidate_columns) < len(other_columns)
                    and other_columns[: len(candidate_columns)] == candidate_columns
                )
                # Exact duplicates (e.g. from a copy-pasted migration) have
                # equal-length, equal column lists — not a "prefix" of one
                # another. Report only the alphabetically-later name against
                # the earlier one, so a pair isn't reported twice.
                is_exact_duplicate = (
                    candidate_columns == other_columns
                    and candidate["index_name"] > other["index_name"]
                )

                if is_strict_prefix:
                    rationale = (
                        f"Columns {candidate_columns} are a strict prefix of "
                        f"index {other['index_name']!r} {other_columns} on the same "
                        "table — any lookup this index serves, that one already covers."
                    )
                elif is_exact_duplicate:
                    rationale = (
                        f"Same columns {candidate_columns} as index {other['index_name']!r} "
                        "on the same table — an exact duplicate."
                    )
                else:
                    continue

                recommendations.append(
                    IndexRecommendation(
                        kind=IndexRecommendationKind.REDUNDANT,
                        severity=Severity.INFO,
                        schema_name=schema,
                        table=table_name,
                        columns=candidate_columns,
                        existing_index_name=candidate["index_name"],
                        rationale=rationale,
                    )
                )
                break
    return recommendations
