"""Message value object/entity within a ChatSession.

TODO: flesh out real fields (role, content, tool calls/results, timestamp)
when `orchestrator` is actually built — see the build order in
docs/architecture/domain-model.md. This placeholder exists only so that
`domain.ports`, `application.send_message`, and the `infrastructure.llm`
adapters have something real to type-check against in the meantime.
"""

from __future__ import annotations

from pydantic import BaseModel


class Message(BaseModel):
    pass  # TODO: role, content, tool calls/results, timestamp.
