"""SchemaGraph aggregate: tables, columns, and foreign keys as a normalized graph.

Less engine variance than execution plans — both Postgres's catalog
(`information_schema` / `pg_catalog`) and SQL Server's
(`INFORMATION_SCHEMA` / `sys.columns`, `sys.foreign_keys`) already describe
roughly the same relational concepts. `raw_data_type` still preserves the
engine-native type name (e.g. `timestamp with time zone` vs. `datetime2`),
since normalizing type names losslessly across engines isn't attempted here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Column(BaseModel):
    name: str
    raw_data_type: str
    """Engine-native type name, e.g. "timestamp with time zone" (Postgres) or
    "datetime2" (SQL Server). Not normalized into a shared type taxonomy."""
    nullable: bool
    default: str | None = None
    is_primary_key: bool = False


class ForeignKey(BaseModel):
    name: str
    columns: list[str]
    references_schema: str
    references_table: str
    references_columns: list[str]


class Table(BaseModel):
    name: str
    schema_name: str
    columns: list[Column]
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    estimated_row_count: int | None = None
    size_bytes: int | None = None


class SchemaGraph(BaseModel):
    """Aggregate root returned by `list_tables`."""

    connection_id: str
    schema_name: str
    tables: list[Table]
