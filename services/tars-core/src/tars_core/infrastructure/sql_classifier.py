"""`sqlglot`-based implementation of `SqlClassifier`.

See docs/adr/0006-approval-gate-via-mcp-elicitation.md.

Fails closed: anything that doesn't parse, or isn't specifically recognized
as read-only, is treated as mutating. Getting this wrong in the "safe"
direction (needlessly asking for approval) is an annoyance; getting it
wrong the other way lets a write through the gate unapproved.

`EXPLAIN` gets special handling: on Postgres, plain `EXPLAIN <stmt>` never
executes `<stmt>`, regardless of what it is — only `EXPLAIN ANALYZE <stmt>`
(bare, or `ANALYZE` inside the `EXPLAIN (...)` options list) actually runs
it. `sqlglot` doesn't parse `EXPLAIN` into a structured tree (it falls back
to a generic `Command` node with the remainder as raw text — verified
empirically against this project's sqlglot version), so that remainder is
inspected directly rather than assumed.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from tars_core.domain.connection import Engine

_READ_ONLY_COMMANDS = {"SHOW", "DESCRIBE", "DESC"}
_LEADING_OPTIONS = re.compile(r"^\s*\(([^)]*)\)\s*")
_LEADING_ANALYZE = re.compile(r"^\s*ANALYZE\b\s*", re.IGNORECASE)
_ANALYZE_WORD = re.compile(r"\bANALYZE\b", re.IGNORECASE)

_SQLGLOT_DIALECT = {
    Engine.POSTGRESQL: "postgres",
    Engine.SQL_SERVER: "tsql",
}
"""`sqlglot` dialect names — an infrastructure-only detail. Callers pass an
`Engine`, never one of these strings directly, so this mapping never leaks
upward into the application layer."""


class SqlglotClassifier:
    """See `tars_core.domain.ports.SqlClassifier` for the contract."""

    def is_mutating(self, sql: str, engine: Engine) -> bool:
        dialect = _SQLGLOT_DIALECT[engine]
        try:
            statements = sqlglot.parse(sql, dialect=dialect)
        except ParseError:
            return True  # can't prove it's safe — fail closed.

        significant = [s for s in statements if s is not None]
        if not significant:
            return True  # nothing parsed — nothing to trust.

        return any(self._statement_is_mutating(stmt, dialect) for stmt in significant)

    def _statement_is_mutating(self, stmt: exp.Expr, dialect: str) -> bool:
        if isinstance(stmt, exp.Select):
            return False
        if isinstance(stmt, exp.Command):
            return self._command_is_mutating(stmt, dialect)
        # INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE, MERGE,
        # EXECUTE (stored procedure calls — unknowable without inspecting
        # the procedure, so treated as mutating), and anything else not
        # explicitly allowlisted above.
        return True

    def _command_is_mutating(self, stmt: exp.Command, dialect: str) -> bool:
        keyword = (stmt.this or "").upper()

        if keyword in _READ_ONLY_COMMANDS:
            return False
        if keyword != "EXPLAIN":
            return True  # unrecognized command — fail closed.

        remainder = self._command_remainder(stmt)
        has_analyze, inner_sql = self._split_explain_options(remainder)
        if not has_analyze:
            return False  # plain EXPLAIN never executes the inner statement.

        try:
            inner = sqlglot.parse_one(inner_sql, dialect=dialect)
        except ParseError:
            return True
        return self._statement_is_mutating(inner, dialect)

    @staticmethod
    def _command_remainder(stmt: exp.Command) -> str:
        expression = stmt.args.get("expression")
        if isinstance(expression, exp.Literal):
            return str(expression.this)
        return ""

    @staticmethod
    def _split_explain_options(remainder: str) -> tuple[bool, str]:
        """Returns (has_analyze, sql_with_the_explain_options_stripped)."""
        options_match = _LEADING_OPTIONS.match(remainder)
        if options_match:
            has_analyze = _ANALYZE_WORD.search(options_match.group(1)) is not None
            return has_analyze, remainder[options_match.end() :]

        analyze_match = _LEADING_ANALYZE.match(remainder)
        if analyze_match:
            return True, remainder[analyze_match.end() :]

        return False, remainder
