"""Query entity and its fingerprint.

`QueryFingerprint` is a normalized, hashable identity for "the same query,"
independent of literal values — needed for the plan-diff differentiator
(deferred past v1, see docs/architecture/overview.md), but defined now
because `classify_statement` and `explain_query` both need a stable way to
refer to "this query" regardless of when the fingerprint gets consumed.

Plain stdlib `dataclasses`, not Pydantic — see
docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from tars_core.domain.connection import Engine


@dataclass(frozen=True, slots=True)
class QueryFingerprint:
    """A hash of the query's normalized form (literals stripped, whitespace
    collapsed). Two executions of "the same query" with different literal
    values produce the same fingerprint.

    NOTE: normalization itself (stripping literals) is an infrastructure
    concern (it needs a SQL parser — see `infrastructure.sql_classifier`,
    which already depends on `sqlglot`) — this value object only defines the
    identity, not how it's computed.
    """

    value: str

    @classmethod
    def of_normalized_sql(cls, normalized_sql: str) -> QueryFingerprint:
        digest = hashlib.sha256(normalized_sql.encode("utf-8")).hexdigest()
        return cls(value=digest)

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class Query:
    sql: str
    engine: Engine
    fingerprint: QueryFingerprint | None = None
    """None until a fingerprint has actually been computed — callers that only
    need to execute or explain the SQL don't need to pay for normalization."""
