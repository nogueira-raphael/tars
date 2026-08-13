import pytest
from tars_core.domain.connection import Engine
from tars_core.infrastructure.sql_classifier import SqlglotClassifier

classifier = SqlglotClassifier()


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM film",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "SELECT * FROM film FOR UPDATE",
        "SHOW search_path",
        "EXPLAIN SELECT * FROM film",
        "EXPLAIN ANALYZE SELECT * FROM film",
        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM film",
        # Plain EXPLAIN never executes the statement it's explaining, on any
        # engine — even one that would be mutating on its own.
        "EXPLAIN INSERT INTO film (id) VALUES (1)",
        "EXPLAIN (COSTS FALSE) DELETE FROM film WHERE id = 1",
    ],
)
def test_read_only_statements_are_not_mutating(sql: str) -> None:
    assert classifier.is_mutating(sql, engine=Engine.POSTGRESQL) is False


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO film (id) VALUES (1)",
        "UPDATE film SET title = 'x' WHERE id = 1",
        "DELETE FROM film WHERE id = 1",
        "CREATE TABLE t (id int)",
        "DROP TABLE t",
        "ALTER TABLE t ADD COLUMN x int",
        "TRUNCATE TABLE t",
        # EXPLAIN ANALYZE genuinely executes the statement being explained —
        # this is the case the naive "EXPLAIN is always safe" rule gets wrong.
        "EXPLAIN ANALYZE INSERT INTO film (id) VALUES (1)",
        "EXPLAIN (ANALYZE) DELETE FROM film WHERE id = 1",
        "EXPLAIN (ANALYZE, BUFFERS) UPDATE film SET title = 'x' WHERE id = 1",
    ],
)
def test_mutating_statements_are_flagged(sql: str) -> None:
    assert classifier.is_mutating(sql, engine=Engine.POSTGRESQL) is True


@pytest.mark.parametrize(
    "sql",
    [
        "not even sql !!!",
        "",
        "   ",
    ],
)
def test_unparseable_or_empty_sql_fails_closed(sql: str) -> None:
    assert classifier.is_mutating(sql, engine=Engine.POSTGRESQL) is True


def test_a_read_only_statement_followed_by_a_mutating_one_is_flagged() -> None:
    # Any statement in a batch being mutating makes the whole call mutating.
    sql = "SELECT * FROM film; DROP TABLE film;"
    assert classifier.is_mutating(sql, engine=Engine.POSTGRESQL) is True


@pytest.mark.parametrize(
    ("sql", "expected"),
    [
        ("SELECT * FROM film", False),
        ("INSERT INTO film (id) VALUES (1)", True),
        ("MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.x = s.x", True),
        ("EXEC sp_who", True),
        ("EXECUTE dbo.MyProc @x = 1", True),
    ],
)
def test_sql_server_dialect(sql: str, expected: bool) -> None:
    assert classifier.is_mutating(sql, engine=Engine.SQL_SERVER) is expected
