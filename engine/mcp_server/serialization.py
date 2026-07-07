"""Serialize a ToolResult (or dry_run dict) into a plain dict for MCP responses.

Never inlines media bytes — artifacts are returned as absolute file paths so the
host agent can hand them to the user or feed them into the next tool.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def _abs_artifacts(artifacts: Any) -> list[str]:
    out: list[str] = []
    for a in artifacts or []:
        try:
            out.append(str(Path(a).resolve()))
        except Exception:
            out.append(str(a))
    return out


def tool_result_to_dict(result: Any) -> dict:
    """Map a ToolResult dataclass (or dict) to a JSON-friendly dict."""
    if is_dataclass(result) and not isinstance(result, type):
        data = asdict(result)
    elif isinstance(result, dict):
        data = dict(result)
    else:
        data = {
            "success": False,
            "error": f"tool returned a non-ToolResult value: {type(result).__name__}",
            "data": {},
            "artifacts": [],
        }

    if "artifacts" in data:
        data["artifacts"] = _abs_artifacts(data.get("artifacts"))

    # One-line, host-displayable summary.
    if data.get("success"):
        n = len(data.get("artifacts") or [])
        cost = data.get("cost_usd") or 0.0
        summary = f"ok — {n} artifact(s)"
        if cost:
            summary += f" — ${cost:.4f}"
        data.setdefault("summary", summary)
    else:
        data.setdefault("summary", f"FAILED: {data.get('error') or 'unknown error'}")
    return data
