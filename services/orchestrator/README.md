# orchestrator

The Conversation bounded context: the thin LLM tool-calling loop, multi-provider support, and the Web UI-facing leg of the approval gate. Never imports `tars-core` directly — reaches diagnostics only through MCP tool calls to `services/mcp-server`.

Fourth service to build, after `tars-core`, `mcp-server`, and the SQL Server provider — see `/docs/architecture/domain-model.md`'s build order. The Orchestrator↔Web UI API contract is deliberately not designed until this step.
