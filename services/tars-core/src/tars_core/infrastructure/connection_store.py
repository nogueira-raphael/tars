"""Fernet + SQLite implementation of `ConnectionRepository`.

The MCP Server's own local store — see docs/adr/0008-credential-storage-two-local-stores.md
and docs/architecture/security.md. Never shared with the Orchestrator's store.

Blocking `sqlite3` calls are pushed to a worker thread via `asyncio.to_thread`
so the event loop isn't blocked — a dedicated async SQLite driver would be
more machinery than a store this small and local needs.
"""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from pathlib import Path

from cryptography.fernet import Fernet

from tars_core.domain.connection import Connection, ConnectionId, Engine

_SCHEMA = """
CREATE TABLE IF NOT EXISTS connections (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    engine TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    database TEXT NOT NULL,
    username TEXT NOT NULL,
    credential_ref TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS credentials (
    ref TEXT PRIMARY KEY,
    encrypted_secret BLOB NOT NULL
);
"""


def _load_or_create_key(key_path: Path) -> bytes:
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    key_path.chmod(0o600)
    return key


def _row_to_connection(row: tuple[object, ...]) -> Connection:
    id_, display_name, engine, host, port, database, username, credential_ref = row
    return Connection(
        id=ConnectionId(value=str(id_)),
        display_name=str(display_name),
        engine=Engine(str(engine)),
        host=str(host),
        port=int(str(port)),
        database=str(database),
        username=str(username),
        credential_ref=str(credential_ref),
    )


class SqliteConnectionRepository:
    """See `tars_core.domain.ports.ConnectionRepository` for the contract."""

    def __init__(self, db_path: Path, key_path: Path) -> None:
        self._db_path = db_path
        self._fernet = Fernet(_load_or_create_key(key_path))
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    async def get(self, connection_id: str) -> Connection:
        return await asyncio.to_thread(self._get_sync, connection_id)

    def _get_sync(self, connection_id: str) -> Connection:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, display_name, engine, host, port, database, username, credential_ref "
                "FROM connections WHERE id = ?",
                (connection_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"no saved connection with id {connection_id!r}")
        return _row_to_connection(row)

    async def list_all(self) -> list[Connection]:
        return await asyncio.to_thread(self._list_all_sync)

    def _list_all_sync(self) -> list[Connection]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, display_name, engine, host, port, database, username, credential_ref "
                "FROM connections ORDER BY display_name"
            ).fetchall()
        return [_row_to_connection(row) for row in rows]

    async def save(self, connection: Connection) -> None:
        await asyncio.to_thread(self._save_sync, connection)

    def _save_sync(self, connection: Connection) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO connections
                    (id, display_name, engine, host, port, database, username, credential_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    display_name = excluded.display_name,
                    engine = excluded.engine,
                    host = excluded.host,
                    port = excluded.port,
                    database = excluded.database,
                    username = excluded.username,
                    credential_ref = excluded.credential_ref
                """,
                (
                    str(connection.id),
                    connection.display_name,
                    connection.engine.value,
                    connection.host,
                    connection.port,
                    connection.database,
                    connection.username,
                    connection.credential_ref,
                ),
            )

    async def delete(self, connection_id: str) -> None:
        await asyncio.to_thread(self._delete_sync, connection_id)

    def _delete_sync(self, connection_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM connections WHERE id = ?", (connection_id,))

    async def save_credential(self, secret: str) -> str:
        return await asyncio.to_thread(self._save_credential_sync, secret)

    def _save_credential_sync(self, secret: str) -> str:
        ref = str(uuid.uuid4())
        encrypted = self._fernet.encrypt(secret.encode("utf-8"))
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO credentials (ref, encrypted_secret) VALUES (?, ?)",
                (ref, encrypted),
            )
        return ref

    async def resolve_credential(self, credential_ref: str) -> str:
        return await asyncio.to_thread(self._resolve_credential_sync, credential_ref)

    def _resolve_credential_sync(self, credential_ref: str) -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT encrypted_secret FROM credentials WHERE ref = ?",
                (credential_ref,),
            ).fetchone()
        if row is None:
            raise KeyError(f"no stored credential with ref {credential_ref!r}")
        return self._fernet.decrypt(bytes(row[0])).decode("utf-8")
