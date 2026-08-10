"""LockTree aggregate: blocking sessions, normalized from `pg_stat_activity`/
`pg_locks` (Postgres) and `sys.dm_exec_requests`/`sys.dm_tran_locks` (SQL
Server).

Modeled as a flat list of sessions with `blocked_by` edges rather than a
literal nested tree: blocking chains are usually tree-shaped in practice,
but a flat graph representation doesn't break if a session is ever blocked
by more than one other, and doesn't need to special-case a deadlock cycle.
The Web UI's renderer builds the visual tree/graph from these edges — the
aggregate name (`LockTree`) describes what gets rendered, not the storage
shape.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SessionState(StrEnum):
    ACTIVE = "active"
    IDLE = "idle"
    IDLE_IN_TRANSACTION = "idle_in_transaction"
    OTHER = "other"


class BlockingSession(BaseModel):
    session_id: str
    database: str | None = None
    query_text: str | None = None
    state: SessionState
    wait_type: str | None = None
    """Engine-native wait type name (e.g. Postgres's `wait_event`, SQL
    Server's `wait_type`) — not normalized into a shared taxonomy."""
    wait_time_ms: float | None = None
    lock_mode: str | None = None
    blocked_by: list[str] = Field(default_factory=list)
    """Session ids of the sessions blocking this one. Empty if not blocked."""
    started_at: datetime | None = None


class LockTree(BaseModel):
    """Aggregate root returned by `active_sessions`/`locks`."""

    connection_id: str
    sessions: list[BlockingSession]
    captured_at: datetime
