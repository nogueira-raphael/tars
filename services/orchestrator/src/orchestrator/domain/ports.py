"""Abstract ports the Conversation domain and application layers depend on.

`application/` may only import from this module, never a concrete
`infrastructure/` implementation — see docs/adr/0010 at the repository root.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from orchestrator.domain.message import Message


class ModelProvider(Protocol):
    """One implementation per LLM SDK (Anthropic, OpenAI, Google, Ollama).

    No multi-provider framework — see docs/adr/0003-thin-custom-orchestrator-not-langgraph.md.
    """

    async def stream(
        self, messages: list[Message], tools: list[object]
    ) -> AsyncIterator[object]: ...


class McpClient(Protocol):
    """Streamable HTTP MCP client, including elicitation handling — see
    docs/adr/0006-approval-gate-via-mcp-elicitation.md.
    """

    async def call_tool(self, name: str, arguments: dict[str, object]) -> object: ...
