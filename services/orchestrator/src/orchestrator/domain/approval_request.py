"""ApprovalRequest: the state machine for a pending MCP elicitation.

States: pending -> approved | denied. Correlates the SSE-relayed approval
from the Web UI back to the MCP Server's `request_state` token. See
docs/adr/0006-approval-gate-via-mcp-elicitation.md.

TODO: define `ApprovalRequest` (id, chat_session_id, request_state, tool
name/args being gated, state, resolved_at).
"""

from __future__ import annotations
