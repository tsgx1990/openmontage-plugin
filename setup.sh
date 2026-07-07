#!/usr/bin/env bash
# One-time manual setup: build the engine dependencies. Optional — the plugin
# also builds them automatically on first use — but running this once after
# install gives you the (slow) dependency build up front, with visible progress.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$DIR}" \
CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$DIR/.data}" \
  "$DIR/bin/openmontage-bootstrap.sh"
echo "Setup complete. Install the plugin in Claude Code and ask it to make a video."
