# 3. Thin custom tool-calling loop, not LangGraph or LangChain

**Status:** Accepted — 2026-08-07

## Context

The Orchestrator needs to run a loop: send the conversation + available tools to an LLM, execute any tool calls via MCP, feed results back, repeat, with a pause for human approval before mutating operations. LangGraph and LangChain are the default reach for "agent loop in Python."

## Decision

A custom, thin tool-calling loop, written in-house. No LangGraph, no LangChain (not even cherry-picking its multi-provider chat model abstraction).

## Rationale

The actual requirement is narrow: a linear loop with tool-calling and one approval gate — not multi-agent branching, not durable checkpointing across long-running graphs. LangGraph's core value (stateful graphs, `interrupt()`-based human-in-the-loop, checkpointing) would justify its complexity for exactly the kind of workflow TARS doesn't have. LangChain sits in an awkward middle: it reduces some boilerplate (unified chat-model interface, MCP tool adapters) but keeps most of the dependency-churn and abstraction overhead of LangGraph, without LangGraph's actual justification for that cost — and it doesn't provide the approval gate natively either, so it doesn't even save the work that mattered most.

This is also why the runtime is MCP-first at all: MCP already standardizes tool discovery/execution, so the orchestrator's job is genuinely small — model call → tool call routing → approval gate → repeat.

## Consequences

- The Orchestrator owns its own `ModelProvider` port with one thin adapter per LLM SDK (`anthropic`, `openai`, `google-genai`, Ollama's OpenAI-compatible REST API) — see `docs/adr/0004-...`.
- No dependency on an external agent framework's release cadence or breaking changes.
- The approval gate (`docs/adr/0006-...`) is implemented directly in the loop and via MCP elicitation, not borrowed from a framework primitive.
