"""OpenMontage MCP server — a thin facade over the tool registry + skill corpus.

Exposes ~9 meta-tools so any MCP host (Claude Code / Codex / OpenCode) can drive
the whole video-production engine from any project. All 93 engine tools are
reached through a single ``run_tool`` — hosts see ~9 tools, not 93, keeping their
context lean while the agent still works discover -> describe -> run.

Run: ``python -m mcp_server.server`` (with cwd = engine root, or rely on the
sys.path insert below). Wire into a host by spawning it over stdio.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

# Make the engine (tools/, lib/, skills/, ...) importable regardless of the
# spawning host's working directory.
_ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGINE_ROOT))

# Default the write-state root to the host's project dir when the host provides
# one (Claude Code exports CLAUDE_PROJECT_DIR) and the operator hasn't pinned
# OPENMONTAGE_PROJECTS_DIR. Must run BEFORE lib.paths is imported — it reads this
# env var at import time. Codex/OpenCode can set OPENMONTAGE_PROJECTS_DIR directly.
import os  # noqa: E402

if not os.environ.get("OPENMONTAGE_PROJECTS_DIR"):
    _host_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if _host_project:
        os.environ["OPENMONTAGE_PROJECTS_DIR"] = str(
            Path(_host_project) / ".openmontage" / "projects"
        )

from mcp.server.fastmcp import FastMCP  # noqa: E402

from tools.tool_registry import registry  # noqa: E402
from tools.base_tool import ToolStatus  # noqa: E402
from mcp_server import corpus as mcp_corpus  # noqa: E402
from mcp_server import paths as mcp_paths  # noqa: E402
from mcp_server.serialization import tool_result_to_dict  # noqa: E402

mcp = FastMCP("openmontage")

_STATE = {"discovered": False}


def _ensure() -> None:
    """Discover all tools once, lazily (keeps server startup instant)."""
    if not _STATE["discovered"]:
        registry.discover()
        _STATE["discovered"] = True


# --------------------------------------------------------------------------
# Inner functions (plain Python, unit-testable without an MCP client).
# The @mcp.tool wrappers below are thin pass-throughs.
# --------------------------------------------------------------------------

def _list_capabilities() -> dict:
    _ensure()
    return registry.provider_menu_summary()


def _list_tools(capability: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    _ensure()
    out: list[dict] = []
    for name in sorted(registry.list_all()):
        tool = registry.get(name)
        if tool is None:
            continue
        if capability and tool.capability != capability:
            continue
        tool_status = tool.get_status().value
        if status and tool_status != status:
            continue
        out.append(
            {
                "name": name,
                "capability": tool.capability,
                "provider": tool.provider,
                "runtime": tool.runtime.value,
                "status": tool_status,
                "best_for": list(tool.best_for or []),
            }
        )
    return out


def _describe_tool(name: str) -> dict:
    _ensure()
    tool = registry.get(name)
    if tool is None:
        return {
            "error": f"unknown tool {name!r}",
            "hint": "call list_tools to see valid names",
        }
    return tool.get_info()


def _run_tool(
    name: str,
    inputs: Any,
    project_id: Optional[str] = None,
    dry_run: bool = False,
    approved: bool = False,
) -> dict:
    _ensure()
    tool = registry.get(name)
    if tool is None:
        return {
            "success": False,
            "error": f"unknown tool {name!r}. Use list_tools to discover names.",
        }
    if not isinstance(inputs, dict):
        return {"success": False, "error": "inputs must be an object/dict"}

    # Availability: never launch a doomed subprocess.
    if tool.get_status() == ToolStatus.UNAVAILABLE:
        info = tool.get_info()
        return {
            "success": False,
            "status": "unavailable",
            "error": f"{name} is unavailable (missing dependency).",
            "install_instructions": info.get("install_instructions", ""),
            "dependencies": info.get("dependencies", []),
        }

    # Sandbox all output paths under the named project dir.
    try:
        project_dir = mcp_paths.resolve_project_dir(project_id)
        safe_inputs = mcp_paths.sandbox_outputs(inputs, project_dir)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    # Preview mode: cost/runtime estimate, no side effects.
    if dry_run:
        preview = tool.dry_run(safe_inputs)
        preview["project_dir"] = str(project_dir)
        return preview

    # Money gate — FAIL CLOSED. Gate anything that (a) costs money, (b) might
    # route to a paid provider, or (c) whose cost we couldn't determine. HYBRID
    # tools are the selectors (image/tts/video) that route to runway/kling/
    # elevenlabs/… — they must NOT slip through just because estimate_cost threw
    # or a provider forgot to override it. Only clearly-free tools with a KNOWN
    # $0 estimate run ungated.
    try:
        est_cost = float(tool.estimate_cost(safe_inputs) or 0.0)
        cost_known = True
    except Exception:
        est_cost, cost_known = 0.0, False
    is_paid = est_cost > 0 or tool.runtime.value in ("api", "hybrid") or not cost_known
    if is_paid and not approved:
        return {
            "success": False,
            "status": "approval_required",
            "estimated_cost_usd": est_cost,
            "cost_known": cost_known,
            "runtime": tool.runtime.value,
            "message": (
                f"{name} may incur cost (est ${est_cost:.4f}"
                f"{'' if cost_known else ', cost undetermined'}, runtime={tool.runtime.value}). "
                "Re-call run_tool with approved=true to proceed, or dry_run=true to preview."
            ),
        }

    # Execute.
    try:
        result = tool.execute(safe_inputs)
    except Exception as exc:  # tool raised — report, don't crash the server
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}
    out = tool_result_to_dict(result)
    out["project_dir"] = str(project_dir)
    return out


# --------------------------------------------------------------------------
# MCP tool registrations.
# --------------------------------------------------------------------------

@mcp.tool()
def list_capabilities() -> dict:
    """Preflight capability menu: which providers/runtimes are configured vs need
    setup. The free stack (ffmpeg / remotion / piper) needs no keys. Call FIRST."""
    return _list_capabilities()


@mcp.tool()
def list_tools(capability: Optional[str] = None, status: Optional[str] = None) -> list:
    """List engine tools, optionally filtered by capability or
    status ('available'/'unavailable'). Returns names + one-line best_for."""
    return _list_tools(capability, status)


@mcp.tool()
def describe_tool(name: str) -> dict:
    """Full contract for one tool, including its input_schema. Call this before
    run_tool so you build inputs that match the schema."""
    return _describe_tool(name)


@mcp.tool()
def run_tool(
    name: str,
    inputs: dict,
    project_id: Optional[str] = None,
    dry_run: bool = False,
    approved: bool = False,
) -> dict:
    """Execute an engine tool by name. Outputs land under the named project
    (relative output paths resolve inside PROJECTS_DIR/<project_id>/). Paid/API
    tools return status='approval_required' unless approved=true; pass
    dry_run=true to preview cost/runtime with no side effects."""
    return _run_tool(name, inputs, project_id, dry_run, approved)


@mcp.tool()
def list_pipelines() -> list:
    """List available production pipelines (explainer, clip-factory, cinematic, ...)."""
    return mcp_corpus.list_pipelines()


@mcp.tool()
def get_pipeline(name: str) -> str:
    """Return a pipeline's YAML manifest (its stages + required director skills)."""
    return mcp_corpus.get_pipeline(name)


@mcp.tool()
def get_agent_guide() -> str:
    """Return AGENT_GUIDE.md, the engine's routing contract. IMPORTANT: ignore its
    instruction to 'write Python that imports tools' — always call run_tool
    instead. When a skill references a 'path/to.md', fetch it via get_skill."""
    return mcp_corpus.get_agent_guide()


@mcp.tool()
def get_skill(rel_path: str) -> str:
    """Fetch a director/meta/core skill markdown, e.g.
    'pipelines/explainer/script-director' or 'meta/reviewer'."""
    return mcp_corpus.get_skill(rel_path)


@mcp.tool()
def get_style(name: str) -> str:
    """Return a visual style playbook YAML, e.g. 'flat-motion-graphics'."""
    return mcp_corpus.get_style(name)


def main() -> None:
    """Entry point — run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
