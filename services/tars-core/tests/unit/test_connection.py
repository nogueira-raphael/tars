from tars_core.domain.connection import Connection, ConnectionId, Engine


def test_connection_never_carries_the_plaintext_credential() -> None:
    connection = Connection(
        id=ConnectionId(value="conn-1"),
        display_name="local pg",
        engine=Engine.POSTGRESQL,
        host="localhost",
        port=5432,
        database="pagila",
        username="postgres",
        credential_ref="cred-1",
    )

    # Connection only ever carries a reference into the encrypted store — see
    # docs/adr/0008-credential-storage-two-local-stores.md. There is no
    # `password`/`secret` field to assert the absence of; the schema itself
    # makes leaking one impossible.
    assert connection.credential_ref == "cred-1"
    assert "password" not in Connection.model_fields
    assert "secret" not in Connection.model_fields


def test_connection_id_stringifies_to_its_value() -> None:
    assert str(ConnectionId(value="conn-1")) == "conn-1"
