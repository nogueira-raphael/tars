"""`active_sessions` / `locks` MCP tool. Never triggers the approval gate."""

from __future__ import annotations


async def active_sessions(connection_id: str) -> object:
    raise NotImplementedError
