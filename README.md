# OpenMontage — Claude Code plugin

Agent-driven video production inside Claude Code: explainers, vertical shorts
(Douyin / TikTok / Shorts), and animations. Powered by the
[OpenMontage](https://github.com/calesthio/OpenMontage) engine (bundled here in
`engine/`) and exposed to Claude Code over MCP.

> ⚠️ **This repo is generated — do not edit it directly.** It is built and
> published from a private engine repo by its one-click publisher. Every release
> resets the entire tree (everything except `.git`/`LICENSE`) to match the
> engine, so any manual change here is discarded on the next publish. Change the
> engine or the plugin templates upstream instead.

## What's inside

- `engine/` — the OpenMontage engine source (Python tools + Remotion composer + the MCP facade `mcp_server/`).
- `.mcp.json` — spawns the engine's MCP server (`openmontage`).
- `skills/openmontage/SKILL.md` — the router Claude follows to make a video.
- `commands/make-video.md` — the `/make-video` slash command.
- `bin/`, `hooks/` — automatic one-time dependency bootstrap (builds a Python venv + Node modules in the plugin's data dir on first use; no manual step needed).

## Install

```
/plugin marketplace add tsgx1990/openmontage-plugin
/plugin install openmontage@openmontage
```

Requirements on the machine: **Python 3.11+**, **Node 18+**, **ffmpeg**, and
**Google Chrome** (Remotion renders with the system Chrome — no separate
browser download). The first use builds the engine dependencies automatically
(a minute or two); everything after is instant.

Then, from any project: `/make-video 30s vertical explainer about X, free path`.
The finished MP4 lands under `<your-project>/.openmontage/projects/`.

## Cost

The **free path** (Piper/macOS-`say` TTS + Remotion + ffmpeg) needs no API keys
and costs **$0**. Paid providers (premium voices/visuals) require approval per
call and their own API keys.

## License

AGPL-3.0 (inherited from OpenMontage).
