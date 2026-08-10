"""Shared severity vocabulary for diagnostics (plan warnings, index recommendations,
lock analysis). Kept separate because it's genuinely shared, not owned by any one
aggregate.
"""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
