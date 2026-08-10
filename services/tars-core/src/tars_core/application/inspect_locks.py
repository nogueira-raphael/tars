"""Use case backing the `active_sessions` / `locks` MCP tool."""

from __future__ import annotations

from dataclasses import dataclass

from tars_core.domain.connection import Connection
from tars_core.domain.locks import LockTree
from tars_core.domain.ports import DatabaseProvider


@dataclass
class InspectLocksUseCase:
    provider: DatabaseProvider

    async def execute(self, connection: Connection) -> LockTree:
        raise NotImplementedError
