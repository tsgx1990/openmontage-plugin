"""OpenMontage MCP facade.

A thin stdio MCP server that exposes OpenMontage's tool registry + skill/pipeline
corpus as a small set of meta-tools, so any MCP host (Claude Code / Codex /
OpenCode) can drive the whole engine from any project — without the engine's
original "the agent writes Python to import tools" assumption.

Additive only: this package wraps the engine (tools/, lib/, skills/, ...) and
does not modify any existing engine file, so it stays upstream-agnostic.
"""

__all__ = ["server", "paths", "corpus", "serialization"]
