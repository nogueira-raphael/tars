from tars_core.domain.schema_graph import Column, ForeignKey, SchemaGraph, Table


def test_table_tracks_which_column_is_the_primary_key() -> None:
    table = Table(
        name="film",
        schema_name="public",
        columns=[
            Column(name="id", raw_data_type="integer", nullable=False, is_primary_key=True),
            Column(name="title", raw_data_type="text", nullable=False),
        ],
    )

    pk_columns = [c.name for c in table.columns if c.is_primary_key]

    assert pk_columns == ["id"]


def test_foreign_key_references_another_table() -> None:
    fk = ForeignKey(
        name="film_actor_actor_id_fkey",
        columns=["actor_id"],
        references_schema="public",
        references_table="actor",
        references_columns=["id"],
    )
    table = Table(
        name="film_actor",
        schema_name="public",
        columns=[Column(name="actor_id", raw_data_type="integer", nullable=False)],
        foreign_keys=[fk],
    )

    assert table.foreign_keys[0].references_table == "actor"


def test_schema_graph_groups_tables_by_schema() -> None:
    graph = SchemaGraph(
        connection_id="conn-1",
        schema_name="public",
        tables=[
            Table(name="film", schema_name="public", columns=[]),
            Table(name="actor", schema_name="public", columns=[]),
        ],
    )

    assert [t.name for t in graph.tables] == ["film", "actor"]
