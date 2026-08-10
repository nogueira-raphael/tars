"""Fernet + SQLite implementation of `ConnectionRepository`.

The MCP Server's own local store — see docs/adr/0008-credential-storage-two-local-stores.md
and docs/architecture/security.md. Never shared with the Orchestrator's store.
"""

from __future__ import annotations

from tars_core.domain.connection import Connection


class SqliteConnectionRepository:
    """See `tars_core.domain.ports.ConnectionRepository` for the contract."""

    async def get(self, connection_id: str) -> Connection:
        raise NotImplementedError

    async def list_all(self) -> list[Connection]:
        raise NotImplementedError

    async def save(self, connection: Connection) -> None:
        raise NotImplementedError

    async def delete(self, connection_id: str) -> None:
        raise NotImplementedError
