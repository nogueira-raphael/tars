"""TARS Conversation bounded context: the thin LLM tool-calling loop and the
approval gate's Web UI-facing leg.

Never imports `tars_core` directly — reaches diagnostics only through an MCP
tool call, via `mcp-server`. See docs/adr/0010 and AGENTS.md at the
repository root.
"""
