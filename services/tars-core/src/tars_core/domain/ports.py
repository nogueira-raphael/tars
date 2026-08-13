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

from tars_core.domain.connection import Connection, Engine
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

    async def explain_query(
        self, connection: Connection, query: Query, *, analyze: bool
    ) -> ExecutionPlan:
        """`analyze` must only be True when the caller (see
        `application.explain_query.ExplainQueryUseCase`) has already
        classified `query` as read-only — `EXPLAIN ANALYZE` genuinely
        executes the statement it explains. Implementations must not decide
        this themselves; they translate the flag, they don't set policy."""
        ...

    async def index_health(
        self, connection: Connection, schema: str
    ) -> list[IndexRecommendation]: ...

    async def active_sessions(self, connection: Connection) -> LockTree: ...

    async def execute_sql(self, connection: Connection, query: Query) -> object: ...


class ConnectionRepository(Protocol):
    """Persists the connection registry *and* the encrypted credentials
    connections reference — see docs/adr/0008-credential-storage-two-local-stores.md,
    which treats these as one store, not two. Implemented via Fernet +
    local SQLite (docs/architecture/security.md).
    """

    async def get(self, connection_id: str) -> Connection: ...

    async def list_all(self) -> list[Connection]: ...

    async def save(self, connection: Connection) -> None: ...

    async def delete(self, connection_id: str) -> None: ...

    async def save_credential(self, secret: str) -> str:
        """Encrypts and stores a secret, returning the `credential_ref` to
        put on a `Connection`. The plaintext `secret` is never itself
        persisted, logged, or returned again — only `resolve_credential`
        can recover it, and only a `DatabaseProvider` should call that,
        immediately before opening a connection."""
        ...

    async def resolve_credential(self, credential_ref: str) -> str:
        """Decrypts and returns the plaintext secret for a `credential_ref`."""
        ...


class SqlClassifier(Protocol):
    """Classifies a SQL statement as mutating or read-only.

    Implemented with `sqlglot` — see docs/adr/0006-approval-gate-via-mcp-elicitation.md.
    Drives whether `execute_sql` triggers the MCP elicitation approval gate,
    and whether `explain_query` is allowed to use `ANALYZE` (which actually
    executes the statement being explained).
    """

    def is_mutating(self, sql: str, engine: Engine) -> bool: ...
