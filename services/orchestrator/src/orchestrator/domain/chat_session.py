"""ChatSession aggregate: a connection + an LLM provider + a message history.

Each chat session binds its own connection+provider pair; multiple concurrent
sessions are supported (see docs/architecture/overview.md, grilling Q13/Q25).
Persisted via `infrastructure.session_store` — chat history is not ephemeral.

TODO: flesh out real fields (id, connection_id, provider, messages) when
`orchestrator` is actually built — see the build order in
docs/architecture/domain-model.md. This placeholder exists only so that
`infrastructure.session_store` and `application.send_message` have
something real to type-check against in the meantime.

Plain stdlib `dataclasses`, not Pydantic — see
docs/adr/0012-domain-layer-uses-dataclasses-not-pydantic.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.domain.message import Message


@dataclass(slots=True)
class ChatSession:
    messages: list[Message] = field(default_factory=list)
    # TODO: id, connection_id, provider, real message history.
