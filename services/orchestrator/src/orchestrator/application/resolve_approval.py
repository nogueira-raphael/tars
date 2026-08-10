"""Resolves a pending `ApprovalRequest` from the Web UI's POST, then resumes
`send_message`'s loop by re-invoking the gated tool with the `request_state`
token attached. See docs/adr/0006-approval-gate-via-mcp-elicitation.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from orchestrator.domain.ports import McpClient


@dataclass
class ResolveApprovalUseCase:
    mcp_client: McpClient

    async def execute(self, approval_request_id: str, approved: bool) -> object:
        raise NotImplementedError
