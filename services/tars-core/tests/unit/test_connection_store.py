from pathlib import Path

import pytest
from tars_core.domain.connection import Connection, ConnectionId, Engine
from tars_core.infrastructure.connection_store import SqliteConnectionRepository


def _make_repo(tmp_path: Path) -> SqliteConnectionRepository:
    return SqliteConnectionRepository(
        db_path=tmp_path / "tars.sqlite3",
        key_path=tmp_path / "secret.key",
    )


def _connection(credential_ref: str = "cred-1") -> Connection:
    return Connection(
        id=ConnectionId(value="conn-1"),
        display_name="local pg",
        engine=Engine.POSTGRESQL,
        host="localhost",
        port=5432,
        database="pagila",
        username="postgres",
        credential_ref=credential_ref,
    )


@pytest.mark.asyncio
async def test_save_then_get_round_trips_a_connection(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    await repo.save(_connection())

    restored = await repo.get("conn-1")

    assert restored == _connection()


@pytest.mark.asyncio
async def test_get_on_a_missing_connection_raises_key_error(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)

    with pytest.raises(KeyError):
        await repo.get("does-not-exist")


@pytest.mark.asyncio
async def test_save_twice_with_the_same_id_updates_in_place(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    await repo.save(_connection())
    updated = _connection()
    updated.display_name = "renamed"
    await repo.save(updated)

    all_connections = await repo.list_all()

    assert len(all_connections) == 1
    assert all_connections[0].display_name == "renamed"


@pytest.mark.asyncio
async def test_delete_removes_the_connection(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    await repo.save(_connection())

    await repo.delete("conn-1")

    with pytest.raises(KeyError):
        await repo.get("conn-1")


@pytest.mark.asyncio
async def test_list_all_orders_by_display_name(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    await repo.save(
        Connection(
            id=ConnectionId(value="b"),
            display_name="zebra",
            engine=Engine.POSTGRESQL,
            host="localhost",
            port=5432,
            database="d",
            username="u",
            credential_ref="r",
        )
    )
    await repo.save(
        Connection(
            id=ConnectionId(value="a"),
            display_name="apple",
            engine=Engine.SQL_SERVER,
            host="localhost",
            port=1433,
            database="d",
            username="u",
            credential_ref="r",
        )
    )

    names = [c.display_name for c in await repo.list_all()]

    assert names == ["apple", "zebra"]


@pytest.mark.asyncio
async def test_credential_round_trips_through_encryption(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)

    ref = await repo.save_credential("s3cr3t-password")
    resolved = await repo.resolve_credential(ref)

    assert resolved == "s3cr3t-password"


@pytest.mark.asyncio
async def test_credential_is_actually_encrypted_at_rest(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    await repo.save_credential("s3cr3t-password")

    raw_file_contents = (tmp_path / "tars.sqlite3").read_bytes()

    assert b"s3cr3t-password" not in raw_file_contents


@pytest.mark.asyncio
async def test_resolve_on_a_missing_credential_raises_key_error(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)

    with pytest.raises(KeyError):
        await repo.resolve_credential("does-not-exist")


def test_reopening_the_store_reuses_the_same_key(tmp_path: Path) -> None:
    # A key generated on first run must survive a restart, or every
    # previously stored credential becomes permanently undecryptable.
    key_path = tmp_path / "secret.key"
    SqliteConnectionRepository(db_path=tmp_path / "tars.sqlite3", key_path=key_path)
    first_key = key_path.read_bytes()

    SqliteConnectionRepository(db_path=tmp_path / "tars.sqlite3", key_path=key_path)
    second_key = key_path.read_bytes()

    assert first_key == second_key
