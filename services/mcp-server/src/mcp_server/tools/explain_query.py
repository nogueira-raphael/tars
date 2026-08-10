"""`explain_query` MCP tool. Never triggers the approval gate — read-only."""

from __future__ import annotations


async def explain_query(connection_id: str, sql: str) -> object:
    """Returns the normalized ExecutionPlan — see docs/adr/0007 at the repository root."""
    raise NotImplementedError
