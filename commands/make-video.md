---
description: Produce a finished video from a one-line brief using the OpenMontage engine (explainer / vertical short / animation).
argument-hint: [brief, e.g. "30s vertical explainer about how neural nets learn, free path"]
---

Use the **openmontage** skill to produce a video for this brief:

> $ARGUMENTS

Follow the skill's flow: read the engine contract via `get_agent_guide` (apply
the Golden rule — always use `run_tool`, never write Python), run
`list_capabilities`, pick the pipeline (`animated-explainer` for explainers,
`clip-factory` for vertical shorts), choose a short `project_id`, work the
stages via `get_skill` + `run_tool`, and default to the **free path** (piper/say
TTS + Remotion + ffmpeg) unless the brief asks for a premium provider. If the
brief needs a paid tool, preview cost with `dry_run` and confirm with the user
before approving. Deliver the final MP4 path from the tool result's `artifacts`.
