"""`sqlglot`-based implementation of `SqlClassifier`.

See docs/adr/0006-approval-gate-via-mcp-elicitation.md.
"""

from __future__ import annotations


class SqlglotClassifier:
    """See `tars_core.domain.ports.SqlClassifier` for the contract."""

    def is_mutating(self, sql: str, dialect: str) -> bool:
        raise NotImplementedError
