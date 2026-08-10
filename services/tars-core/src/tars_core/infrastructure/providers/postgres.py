"""PostgreSQL implementation of `DatabaseProvider`, via `psycopg3` (async).

Build this one first — see docs/architecture/domain-model.md's build order.
TODO: implement against the normalized schema once docs/adr/0007 is resolved.
"""

from __future__ import annotations

from tars_core.domain.connection import Connection
from tars_core.domain.execution_plan import ExecutionPlan
from tars_core.domain.index_recommendation import IndexRecommendation
from tars_core.domain.locks import LockTree
from tars_core.domain.query import Query
from tars_core.domain.schema_graph import SchemaGraph


class PostgresProvider:
    """See `tars_core.domain.ports.DatabaseProvider` for the contract."""

    async def list_schemas(self, connection: Connection) -> list[str]:
        raise NotImplementedError

    async def list_tables(self, connection: Connection, schema: str) -> SchemaGraph:
        raise NotImplementedError

    async def explain_query(self, connection: Connection, query: Query) -> ExecutionPlan:
        raise NotImplementedError

    async def index_health(self, connection: Connection, schema: str) -> list[IndexRecommendation]:
        raise NotImplementedError

    async def active_sessions(self, connection: Connection) -> LockTree:
        raise NotImplementedError

    async def execute_sql(self, connection: Connection, query: Query) -> object:
        raise NotImplementedError
