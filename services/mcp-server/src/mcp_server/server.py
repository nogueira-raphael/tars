"""MCP SDK wiring — Streamable HTTP transport (SSE is deprecated by the MCP
spec, stdio reserved for standalone use). See docs/architecture/overview.md.

TODO: register the tools in `mcp_server.tools`, wire `auth.verify_token`
into the transport layer, and instantiate `tars_core`'s use cases with the
Postgres/SQL Server providers.
"""

from __future__ import annotations


def create_app() -> object:
    raise NotImplementedError
