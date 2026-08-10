from tars_core.domain.connection import Engine
from tars_core.domain.query import Query, QueryFingerprint


def test_fingerprint_is_deterministic_for_the_same_normalized_sql() -> None:
    a = QueryFingerprint.of_normalized_sql("SELECT * FROM film WHERE id = ?")
    b = QueryFingerprint.of_normalized_sql("SELECT * FROM film WHERE id = ?")

    assert a == b
    assert str(a) == str(b)


def test_fingerprint_differs_for_different_normalized_sql() -> None:
    a = QueryFingerprint.of_normalized_sql("SELECT * FROM film WHERE id = ?")
    b = QueryFingerprint.of_normalized_sql("SELECT * FROM actor WHERE id = ?")

    assert a != b


def test_query_fingerprint_is_optional_until_computed() -> None:
    query = Query(sql="SELECT 1", engine=Engine.POSTGRESQL)

    assert query.fingerprint is None
