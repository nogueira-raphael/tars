"""Use case deciding whether a SQL statement passed to `execute_sql` is mutating.

Drives the MCP elicitation approval gate — see
docs/adr/0006-approval-gate-via-mcp-elicitation.md. Automatic classification only;
never trusts caller-declared intent.
"""

from __future__ import annotations

from dataclasses import dataclass

from tars_core.domain.ports import SqlClassifier


@dataclass
class ClassifyStatementUseCase:
    classifier: SqlClassifier

    def execute(self, sql: str, dialect: str) -> bool:
        """Returns True if the statement is mutating (not read-only)."""
        raise NotImplementedError
