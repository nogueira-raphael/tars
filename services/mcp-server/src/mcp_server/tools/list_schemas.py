"""`list_schemas` / `list_tables` MCP tools. Never trigger the approval gate."""

from __future__ import annotations


async def list_schemas(connection_id: str) -> object:
    raise NotImplementedError


async def list_tables(connection_id: str, schema: str) -> object:
    raise NotImplementedError
