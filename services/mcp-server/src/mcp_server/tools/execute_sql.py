"""`execute_sql` MCP tool — the only one that can write.

Read-only by default. Mutating statements (classified via
`tars_core.application.classify_statement`) return an `InputRequiredResult`
+ `request_state` token instead of executing — see
docs/adr/0006-approval-gate-via-mcp-elicitation.md. Only re-invocation with
a resolved `request_state` actually executes.
"""

from __future__ import annotations


async def execute_sql(connection_id: str, sql: str, request_state: str | None = None) -> object:
    raise NotImplementedError
