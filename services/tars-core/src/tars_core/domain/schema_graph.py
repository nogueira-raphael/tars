"""SchemaGraph aggregate: tables, columns, and foreign keys as a normalized graph.

Less engine variance than execution plans — both Postgres's catalog
(`information_schema` / `pg_catalog`) and SQL Server's
(`INFORMATION_SCHEMA` / `sys.columns`, `sys.foreign_keys`) already describe
roughly the same relational concepts. `raw_data_type` still preserves the
engine-native type name (e.g. `timestamp with time zone` vs. `datetime2`),
since normalizing type names losslessly across engines isn't attempted here.

Plain stdlib `dataclasses`, not Pydantic — see
docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Column:
    name: str
    raw_data_type: str
    """Engine-native type name, e.g. "timestamp with time zone" (Postgres) or
    "datetime2" (SQL Server). Not normalized into a shared type taxonomy."""
    nullable: bool
    default: str | None = None
    is_primary_key: bool = False


@dataclass(slots=True)
class ForeignKey:
    name: str
    columns: list[str]
    references_schema: str
    references_table: str
    references_columns: list[str]


@dataclass(slots=True)
class Table:
    name: str
    schema_name: str
    columns: list[Column]
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    estimated_row_count: int | None = None
    size_bytes: int | None = None


@dataclass(slots=True)
class SchemaGraph:
    """Aggregate root returned by `list_tables`."""

    connection_id: str
    schema_name: str
    tables: list[Table]
