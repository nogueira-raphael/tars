"""Shared bearer token validation — gates every client uniformly, including
external standalone ones (e.g. Claude Desktop). See docs/architecture/security.md.
"""

from __future__ import annotations


def verify_token(token: str) -> bool:
    raise NotImplementedError
