"""Project-dir resolution + output-path sandboxing for the MCP facade.

Reuses ``lib.paths.PROJECTS_DIR`` (the ``OPENMONTAGE_PROJECTS_DIR`` override) as
the single write-state root — the only path in the engine designed to be
relocated. A ``run_tool`` call names a ``project_id``; all of its outputs land
under ``PROJECTS_DIR/<project_id>/``.

Relative output paths in a tool's inputs are rewritten to absolute paths inside
that project dir; traversal outside it is rejected. Absolute *input* paths (the
source media the user references) are left untouched.
"""

from __future__ import annotations

import re
from pathlib import Path

from lib.paths import PROJECTS_DIR

# Input keys that name a WRITE destination (kept deliberately narrow so we never
# rewrite an INPUT dir like clip_search's `corpus_dir`).
_OUTPUT_KEYS = ("output_path", "output_dir", "out_path", "output_file", "dest_path")

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
# Skill-convention prefix: director skills often write to "projects/<name>/...".
# Under the plugin model PROJECTS_DIR is already the projects root and the
# project_id is the subdir, so strip that prefix to avoid double-nesting.
_SKILL_PREFIX = re.compile(r"^projects/[^/]+/(.*)$")


def resolve_project_dir(project_id: str | None) -> Path:
    """Return (and create) ``PROJECTS_DIR/<project_id>``, guarding traversal."""
    pid = (project_id or "default").strip()
    if not _SAFE_ID.match(pid):
        raise ValueError(
            f"invalid project_id {project_id!r}: use letters, digits, '.', '_', '-' only"
        )
    root = PROJECTS_DIR.resolve()
    project_dir = (root / pid).resolve()
    if project_dir != root and root not in project_dir.parents:
        raise ValueError("project_id escapes PROJECTS_DIR")
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def sandbox_outputs(inputs: dict, project_dir: Path) -> dict:
    """Copy ``inputs`` with relative output paths rewritten under ``project_dir``.

    - relative ``x/y.wav`` -> ``project_dir/x/y.wav``
    - skill-style ``projects/<name>/x.wav`` -> ``project_dir/x.wav`` (prefix stripped)
    - absolute path already under ``project_dir`` -> kept as-is
    - absolute path elsewhere / ``..`` escape -> ``ValueError``
    """
    if not isinstance(inputs, dict):
        return inputs
    out = dict(inputs)
    root = project_dir.resolve()
    for key in _OUTPUT_KEYS:
        val = out.get(key)
        if not isinstance(val, str) or not val:
            continue
        p = Path(val)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            match = _SKILL_PREFIX.match(val)
            rel = match.group(1) if match else val
            resolved = (project_dir / rel).resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(
                f"{key}={val!r} escapes the project directory {root}"
            )
        resolved.parent.mkdir(parents=True, exist_ok=True)
        out[key] = str(resolved)
    return out
