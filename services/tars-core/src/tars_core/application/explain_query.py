"""Use case backing the `explain_query` MCP tool.

Never triggers the approval gate (see docs/architecture/overview.md's tool
table) — that's only true because this use case, not the provider, decides
whether `ANALYZE` is safe to use. A query classified as mutating still gets
explained, just without `ANALYZE`, so it's never actually executed.
"""

from __future__ import annotations

from dataclasses import dataclass

from tars_core.domain.connection import Connection
from tars_core.domain.execution_plan import ExecutionPlan
from tars_core.domain.ports import DatabaseProvider, SqlClassifier
from tars_core.domain.query import Query


@dataclass
class ExplainQueryUseCase:
    provider: DatabaseProvider
    classifier: SqlClassifier

    async def execute(self, connection: Connection, query: Query) -> ExecutionPlan:
        is_mutating = self.classifier.is_mutating(query.sql, connection.engine)
        return await self.provider.explain_query(connection, query, analyze=not is_mutating)
