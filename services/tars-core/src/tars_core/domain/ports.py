"""Abstract ports the domain and application layers depend on.

`application/` may only import from this module, never a concrete
`infrastructure/` implementation — see docs/adr/0010 at the repository root.

Return types reference domain objects (`ExecutionPlan`, `SchemaGraph`,
`LockTree`) whose field-level shape isn't finalized yet — see
docs/adr/0007-normalized-diagnostic-schema.md. The method signatures below
are stable regardless of that; only the payload shapes are still open.
"""

from __future__ import annotations

from typing import Protocol

from tars_core.domain.connection import Connection
from tars_core.domain.execution_plan import ExecutionPlan
from tars_core.domain.index_recommendation import IndexRecommendation
from tars_core.domain.locks import LockTree
from tars_core.domain.query import Query
from tars_core.domain.schema_graph import SchemaGraph


class DatabaseProvider(Protocol):
    """One implementation per supported engine (Postgres, SQL Server, ...).

    Implemented in `infrastructure/providers/`. Never imported directly by
    `application/` — only through this Protocol.
    """

    async def list_schemas(self, connection: Connection) -> list[str]: ...

    async def list_tables(self, connection: Connection, schema: str) -> SchemaGraph: ...

    async def explain_query(self, connection: Connection, query: Query) -> ExecutionPlan: ...

    async def index_health(
        self, connection: Connection, schema: str
    ) -> list[IndexRecommendation]: ...

    async def active_sessions(self, connection: Connection) -> LockTree: ...

    async def execute_sql(self, connection: Connection, query: Query) -> object: ...


class ConnectionRepository(Protocol):
    """Persists the connection registry. Implemented via encrypted local SQLite
    — see docs/architecture/security.md.
    """

    async def get(self, connection_id: str) -> Connection: ...

    async def list_all(self) -> list[Connection]: ...

    async def save(self, connection: Connection) -> None: ...

    async def delete(self, connection_id: str) -> None: ...


class SqlClassifier(Protocol):
    """Classifies a SQL statement as mutating or read-only.

    Implemented with `sqlglot` — see docs/adr/0006-approval-gate-via-mcp-elicitation.md.
    Drives whether `execute_sql` triggers the MCP elicitation approval gate.
    """

    def is_mutating(self, sql: str, dialect: str) -> bool: ...
