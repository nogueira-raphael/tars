"""Streamable HTTP MCP client, including elicitation handling — receives
`InputRequiredResult` + `request_state` from the MCP Server and surfaces it
to `application.send_message`'s loop. See
docs/adr/0006-approval-gate-via-mcp-elicitation.md.
"""

from __future__ import annotations


class StreamableHttpMcpClient:
    """See `orchestrator.domain.ports.McpClient` for the contract."""

    async def call_tool(self, name: str, arguments: dict[str, object]) -> object:
        raise NotImplementedError
