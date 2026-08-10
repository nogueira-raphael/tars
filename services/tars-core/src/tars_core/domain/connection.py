"""Connection entity: a saved, credentialed handle to a target database.

The credential itself (password/secret) never lives on this object — only a
reference to it in the encrypted local store. See docs/architecture/security.md
and docs/adr/0008-credential-storage-two-local-stores.md.

Plain stdlib `dataclasses`, not Pydantic — see
docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Engine(StrEnum):
    """Supported database engines. See docs/adr/0001-postgres-and-sql-server-first.md
    for why these two are first; add new members here as providers are added,
    never infer the engine from a connection string.
    """

    POSTGRESQL = "postgresql"
    SQL_SERVER = "sql_server"


@dataclass(frozen=True, slots=True)
class ConnectionId:
    """Opaque identifier — a value object, not just a bare str, so callers can't
    accidentally pass a table name or query id where a connection id is expected.
    """

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class Connection:
    """A saved connection. `credential_ref` points into the MCP Server's local
    encrypted store (`infrastructure.connection_store`) — this object itself is
    safe to log, serialize, and send over MCP without leaking a secret.
    """

    id: ConnectionId
    display_name: str
    engine: Engine
    host: str
    port: int
    database: str
    username: str
    credential_ref: str
