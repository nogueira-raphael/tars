"""`ModelProvider` adapter over Ollama's local OpenAI-compatible REST API
(via `httpx`, no dedicated SDK)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from orchestrator.domain.message import Message


class OllamaProvider:
    """See `orchestrator.domain.ports.ModelProvider` for the contract."""

    async def stream(self, messages: list[Message], tools: list[object]) -> AsyncIterator[object]:
        raise NotImplementedError
