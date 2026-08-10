"""The thin tool-calling loop: send messages + tool schemas to the configured
LLM, execute any tool calls via `McpClient`, handle `InputRequiredResult`
elicitation responses by pausing and relaying to the Web UI, feed results
back, repeat. See docs/architecture/overview.md.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from orchestrator.domain.chat_session import ChatSession
from orchestrator.domain.ports import McpClient, ModelProvider


@dataclass
class SendMessageUseCase:
    model_provider: ModelProvider
    mcp_client: McpClient

    async def execute(self, session: ChatSession, user_message: str) -> AsyncIterator[object]:
        """Yields streamable events for the Orchestrator's SSE endpoint to forward."""
        raise NotImplementedError
