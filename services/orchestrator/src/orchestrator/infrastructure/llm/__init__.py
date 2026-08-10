"""One `ModelProvider` adapter per LLM SDK. Official SDKs only, no multi-provider
framework — see docs/adr/0003-thin-custom-orchestrator-not-langgraph.md.

Modules: anthropic.py, openai.py, google.py, ollama.py (ollama via its
OpenAI-compatible REST API, no dedicated SDK needed).
"""
