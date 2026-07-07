#!/usr/bin/env bash
# MCP server launcher: guarantees the engine venv exists (builds it on first
# run), then execs the stdio MCP server. Using a launcher — rather than pointing
# .mcp.json straight at the venv python — removes any race between the venv
# bootstrap and the server spawn.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$DIR/.." && pwd)}"
DATA="${CLAUDE_PLUGIN_DATA:-$ROOT/.data}"

"$DIR/openmontage-bootstrap.sh"    # fast no-op once built

# Run from the engine dir so `python -m mcp_server.server` resolves regardless of
# whether the host honored .mcp.json's `cwd`.
cd "$ROOT/engine"
exec "$DATA/venv/bin/python" -m mcp_server.server
