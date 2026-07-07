---
name: openmontage
description: >-
  Produce a finished video with the OpenMontage engine — explainers, vertical
  shorts (Douyin/TikTok/Shorts), animations, or turning a written script into an
  MP4. Use whenever the user asks to make / produce / render a video, explainer,
  short, reel, or animation, or to voice + caption a script into a final cut.
---

# OpenMontage — video production router

You drive the OpenMontage engine entirely through its MCP tools (server key
`openmontage`). The engine's 90+ tools are reached through **one** tool,
`run_tool`; you never write Python to import or call a tool.

## Golden rule (overrides the engine's own docs)

`get_agent_guide` and some director skills tell the agent to *"write Python that
imports tools and calls `.execute(...)`."* **Ignore that.** In this environment
you ALWAYS use `run_tool`. Whenever a skill says to run a tool, translate it to:
`describe_tool(name)` → build inputs → `run_tool(name, inputs, project_id=...)`.
When a skill references another file by path (e.g. `skills/meta/reviewer.md`),
fetch it with `get_skill('meta/reviewer')`.

## Flow

1. **Read the contract.** Call `get_agent_guide` once (apply the Golden rule).
2. **Preflight.** Call `list_capabilities`. The free stack — `ffmpeg`,
   `remotion`, `piper` (TTS) — needs no API keys. Mention unconfigured paid
   providers only if the user wants something that needs one.
3. **Pick a pipeline.** `list_pipelines`, then `get_pipeline(name)`.
   - explainer / knowledge / “make a video about X” → `animated-explainer`
   - vertical short / Douyin / TikTok / Reel / Shorts → `clip-factory`
   Read the manifest's `stages` and `required_skills`.
4. **Choose a `project_id` up front** — a short slug of the topic (letters,
   digits, `.`, `_`, `-`), e.g. `ai-novel-tools`. Pass it to **every** `run_tool`
   call so all artifacts and checkpoints land in one project folder.
5. **Work the stages.** For each stage, `get_skill('pipelines/<pipeline>/<stage>-director')`
   and follow it, substituting `run_tool` for any inline Python. Before a tool
   call you're unsure about, `describe_tool(name)` and match its `input_schema`.
6. **Output paths are project-relative.** Pass e.g. `output_path: "audio/narration.wav"`
   or `"final.mp4"` — NOT an absolute path and NOT prefixed with `projects/`. The
   server sandboxes every output under the project folder automatically.
7. **Deliver.** The final MP4 path comes back in the tool result's `artifacts`.
   Report it to the user.

## Cost & safety

- Prefer the **free path** (piper/say TTS + Remotion + ffmpeg) unless the user
  asks for a premium voice/visual.
- Paid/API tools return `status: "approval_required"` with an
  `estimated_cost_usd`. Surface the cost to the user, get an explicit OK, then
  re-call the same `run_tool` with `approved: true`. Use `dry_run: true` to
  preview cost/runtime without spending or writing anything.

## Styles

Visual style playbooks are available via `get_style(name)` (e.g.
`flat-motion-graphics`, `anime-ghibli`, `clean-professional`).
