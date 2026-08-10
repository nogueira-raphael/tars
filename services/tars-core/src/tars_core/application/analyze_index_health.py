"""Use case backing the `index_health` MCP tool. Recommendation-only, no apply path
— see docs/architecture/overview.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from tars_core.domain.connection import Connection
from tars_core.domain.index_recommendation import IndexRecommendation
from tars_core.domain.ports import DatabaseProvider


@dataclass
class AnalyzeIndexHealthUseCase:
    provider: DatabaseProvider

    async def execute(self, connection: Connection, schema: str) -> list[IndexRecommendation]:
        raise NotImplementedError
