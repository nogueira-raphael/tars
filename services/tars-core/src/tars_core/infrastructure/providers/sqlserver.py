"""SQL Server implementation of `DatabaseProvider`, via `mssql-python`.

Built second, after the Postgres provider proves the abstraction — see
docs/adr/0001-postgres-and-sql-server-first.md and docs/architecture/
domain-model.md's build order.
"""

from __future__ import annotations

from tars_core.domain.connection import Connection
from tars_core.domain.execution_plan import ExecutionPlan
from tars_core.domain.index_recommendation import IndexRecommendation
from tars_core.domain.locks import LockTree
from tars_core.domain.query import Query
from tars_core.domain.schema_graph import SchemaGraph


class SqlServerProvider:
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
