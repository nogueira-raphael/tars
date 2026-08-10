"""`index_health` MCP tool. Recommendation-only, never triggers the approval gate."""

from __future__ import annotations


async def index_health(connection_id: str, schema: str) -> object:
    raise NotImplementedError
