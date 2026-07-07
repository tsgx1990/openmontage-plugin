#!/usr/bin/env bash
# Build the OpenMontage engine dependencies (Python venv + Node modules) into the
# plugin's PERSISTENT data dir, once. Idempotent and near-instant when already
# built (it exits early unless requirements.txt changed). Safe to call on every
# session start and from the server launcher.
set -euo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA="${CLAUDE_PLUGIN_DATA:-$ROOT/.data}"
ENGINE="$ROOT/engine"
VENV="$DATA/venv"
STAMP="$DATA/.deps-stamp"

mkdir -p "$DATA"

req_hash=""
if [ -f "$ENGINE/requirements.txt" ]; then
  if command -v shasum >/dev/null 2>&1; then
    req_hash="$(shasum "$ENGINE/requirements.txt" | awk '{print $1}')"
  else
    req_hash="$(sha1sum "$ENGINE/requirements.txt" | awk '{print $1}')"
  fi
fi
cur="$(cat "$STAMP" 2>/dev/null || true)"

# Already built and requirements unchanged -> nothing to do.
if [ -x "$VENV/bin/python" ] && [ "$cur" = "$req_hash" ]; then
  exit 0
fi

echo "[openmontage] building engine deps (first run — a minute or two)…" >&2

# --- Python venv -----------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
  uv venv "$VENV" >/dev/null
  uv pip install --python "$VENV/bin/python" -r "$ENGINE/requirements.txt" "mcp>=1.2" >/dev/null
else
  PY="$(command -v python3.11 || command -v python3.12 || command -v python3 || true)"
  if [ -z "$PY" ]; then
    echo "[openmontage] ERROR: need Python 3.11+ (or 'uv') on PATH." >&2
    exit 1
  fi
  "$PY" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet -r "$ENGINE/requirements.txt" "mcp>=1.2"
fi

# --- Node deps for Remotion (optional; only needed for video_compose) -------
if [ -d "$ENGINE/remotion-composer" ] && [ ! -d "$ENGINE/remotion-composer/node_modules" ]; then
  if command -v npm >/dev/null 2>&1; then
    ( cd "$ENGINE/remotion-composer" && npm install --no-audit --no-fund >/dev/null 2>&1 ) \
      || echo "[openmontage] WARN: 'npm install' failed in engine/remotion-composer — Remotion renders need it." >&2
  else
    echo "[openmontage] WARN: 'npm' not found — install Node 18+ for Remotion renders." >&2
  fi
fi

echo "$req_hash" > "$STAMP"
echo "[openmontage] engine ready." >&2
