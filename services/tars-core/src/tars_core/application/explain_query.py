"""Use case backing the `explain_query` MCP tool."""

from __future__ import annotations

from dataclasses import dataclass

from tars_core.domain.connection import Connection
from tars_core.domain.execution_plan import ExecutionPlan
from tars_core.domain.ports import DatabaseProvider
from tars_core.domain.query import Query


@dataclass
class ExplainQueryUseCase:
    provider: DatabaseProvider

    async def execute(self, connection: Connection, query: Query) -> ExecutionPlan:
        raise NotImplementedError
