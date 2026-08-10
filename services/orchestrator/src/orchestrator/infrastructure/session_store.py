"""Fernet + SQLite store for chat history, sessions, and LLM API keys.

The Orchestrator's own local store — separate from the MCP Server's, which
holds database credentials. Never merge these. See
docs/adr/0008-credential-storage-two-local-stores.md.
"""

from __future__ import annotations

from orchestrator.domain.chat_session import ChatSession


class SqliteSessionStore:
    async def get_session(self, session_id: str) -> ChatSession:
        raise NotImplementedError

    async def save_session(self, session: ChatSession) -> None:
        raise NotImplementedError
