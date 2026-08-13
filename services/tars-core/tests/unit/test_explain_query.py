from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
from tars_core.application.explain_query import ExplainQueryUseCase
from tars_core.domain.connection import Connection, ConnectionId, Engine
from tars_core.domain.execution_plan import ExecutionPlan, PlanNode, PlanOperation
from tars_core.domain.index_recommendation import IndexRecommendation
from tars_core.domain.locks import LockTree
from tars_core.domain.query import Query
from tars_core.domain.schema_graph import SchemaGraph
from tars_core.infrastructure.sql_classifier import SqlglotClassifier


@dataclass
class _RecordingProvider:
    """A fake `DatabaseProvider` that only cares about `explain_query`,
    recording whether it was asked to analyze. The other methods exist
    purely to satisfy the Protocol structurally — this use case never
    calls them.
    """

    seen_analyze: list[bool] = field(default_factory=list)

    async def explain_query(
        self, connection: Connection, query: Query, *, analyze: bool
    ) -> ExecutionPlan:
        self.seen_analyze.append(analyze)
        root = PlanNode(
            node_id="0", operation=PlanOperation.SEQUENTIAL_SCAN, raw_operation_name="Seq Scan"
        )
        return ExecutionPlan(
            query=query,
            connection_id=str(connection.id),
            root=root,
            is_actual=analyze,
            captured_at=datetime.now(UTC),
        )

    async def list_schemas(self, connection: Connection) -> list[str]:
        raise NotImplementedError("not exercised by this test")

    async def list_tables(self, connection: Connection, schema: str) -> SchemaGraph:
        raise NotImplementedError("not exercised by this test")

    async def index_health(self, connection: Connection, schema: str) -> list[IndexRecommendation]:
        raise NotImplementedError("not exercised by this test")

    async def active_sessions(self, connection: Connection) -> LockTree:
        raise NotImplementedError("not exercised by this test")

    async def execute_sql(self, connection: Connection, query: Query) -> object:
        raise NotImplementedError("not exercised by this test")


def _connection() -> Connection:
    return Connection(
        id=ConnectionId(value="conn-1"),
        display_name="local pg",
        engine=Engine.POSTGRESQL,
        host="localhost",
        port=5432,
        database="pagila",
        username="postgres",
        credential_ref="cred-1",
    )


@pytest.mark.asyncio
async def test_read_only_query_is_explained_with_analyze() -> None:
    provider = _RecordingProvider()
    use_case = ExplainQueryUseCase(provider=provider, classifier=SqlglotClassifier())

    await use_case.execute(_connection(), Query(sql="SELECT * FROM film", engine=Engine.POSTGRESQL))

    assert provider.seen_analyze == [True]


@pytest.mark.asyncio
async def test_mutating_query_is_explained_without_analyze_so_it_never_executes() -> None:
    provider = _RecordingProvider()
    use_case = ExplainQueryUseCase(provider=provider, classifier=SqlglotClassifier())

    await use_case.execute(_connection(), Query(sql="DELETE FROM film", engine=Engine.POSTGRESQL))

    assert provider.seen_analyze == [False]
