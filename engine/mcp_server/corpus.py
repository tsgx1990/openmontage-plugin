"""Serve OpenMontage's routing / skill / pipeline / style corpus from REPO_ROOT.

The engine's *intelligence* (AGENT_GUIDE routing, 12 pipeline manifests, ~50
director-skill markdowns, style playbooks) stays in the fork as the single
source of truth and is streamed to the host on demand — so upstream edits flow
through with zero adapter changes, and repo-relative references inside a skill
resolve here, server-side, against REPO_ROOT.
"""

from __future__ import annotations

from pathlib import Path

from lib.paths import REPO_ROOT


def _read(rel: str) -> str:
    """Read a repo-relative text file, refusing any path that escapes REPO_ROOT."""
    root = REPO_ROOT.resolve()
    path = (root / rel).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"path {rel!r} escapes the engine root")
    if not path.is_file():
        raise FileNotFoundError(f"{rel} not found under the engine")
    return path.read_text(encoding="utf-8", errors="replace")


def get_agent_guide() -> str:
    return _read("AGENT_GUIDE.md")


def list_pipelines() -> list[dict]:
    """List pipeline manifests (name + path) from pipeline_defs/."""
    defs = (REPO_ROOT / "pipeline_defs").resolve()
    out: list[dict] = []
    if defs.is_dir():
        for f in sorted(defs.glob("*.yaml")):
            out.append({"name": f.stem, "path": f"pipeline_defs/{f.name}"})
    return out


def get_pipeline(name: str) -> str:
    stem = name[:-5] if name.endswith(".yaml") else name
    return _read(f"pipeline_defs/{stem}.yaml")


def get_skill(rel_path: str) -> str:
    """Fetch a director/meta/core skill markdown.

    Accepts forms like 'pipelines/explainer/script-director', 'meta/reviewer',
    with or without a leading 'skills/' and with or without the '.md' suffix.
    """
    rel = rel_path.strip().lstrip("/")
    if rel.startswith("skills/"):
        rel = rel[len("skills/"):]
    if not rel.endswith(".md"):
        rel += ".md"
    return _read(f"skills/{rel}")


def get_style(name: str) -> str:
    stem = name[:-5] if name.endswith(".yaml") else name
    return _read(f"styles/{stem}.yaml")
