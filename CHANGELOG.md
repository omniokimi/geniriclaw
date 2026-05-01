# Changelog

All notable changes to this fork are documented here. The omniokimi/geniriclaw fork extends the upstream igorfabrus/geniriclaw with quality-of-life features for production multi-agent deployments.

## [2.0.0] — 2026-05-01 — Extended Edition

The first release after splitting v1.0-light. Adds four substantial v2 features:

### Added

- **AI-generated startup greeting** (`geniriclaw/text/response_format.py`)
  On `first_start`, the bot now generates a 1–2 sentence Russian greeting via Claude (Haiku) that references the last conversation context from `~/.geniriclaw/workspace/memory_system/MAINMEMORY.md`. Result is cached by sha256 of MAINMEMORY in `~/.geniriclaw/state/last_greeting.json` — re-generation only happens when memory actually changes. Falls back to a random phrase from `_FIRST_START_PHRASES` if Claude is unavailable.
  Note: `system_reboot` and `service_restart` are now silent (no message) — avoids interrupting an ongoing conversation. Use `v1.0-light` if you prefer the old "I'm back" reboot phrases.

- **Humanised tool-progress indicators** (`geniriclaw/messenger/telegram/{edit_streaming,message_dispatch}.py`)
  Tool-call indicator no longer prefixed with «Инструмент |» — only the tool name in a `<blockquote>` (cleaner, less robotic). System status labels softened: «Восстанавливаюсь» → «Меняю подход», «Компакт» → «Привожу мысли в порядок», «Близок таймаут» → «Ещё чуть-чуть».

- **Parallel chat via TaskHub** (`geniriclaw/{config,messenger/telegram/middleware,messenger/telegram/app}.py`)
  New config flag `tasks.parallel_chat_when_busy` (default `False`). When enabled, a user message arriving while the per-chat lock is held is dispatched as an independent background `TaskHub` task (new Claude session) instead of waiting in the queue. Each parallel task gets its own session id; result is delivered back to the chat via `on_task_result` — OpenClaw-style parallel chat lanes. Fail-safe: any submit error falls back to the legacy queue.

- **Camofox-browser integration** (`geniriclaw/infra/camofox/`, `geniriclaw/cli_commands/camofox.py`, `geniriclaw/_home_defaults/{launchd,workspace/skills/camofox-browser}/`)
  First-class integration with [jo-inc/camofox-browser](https://github.com/jo-inc/camofox-browser) — a Node.js REST server wrapping Camoufox (Firefox fork with C++ stealth fingerprinting). Lets the agent see protected sites that fail with `web_fetch` (LinkedIn HTTP 999, JS-rendered pages, anti-bot walls).
  - New CLI: `geniriclaw camofox install / start / stop / restart / status / uninstall [--purge]`
  - LaunchAgent template `dev.geniri.camofox.plist` with `KeepAlive: Crashed=true`, `ThrottleInterval=10`
  - Python client `geniriclaw.infra.camofox.CamofoxClient` (httpx, context-manager) — `health/navigate/snapshot/click/type_text/screenshot/console_logs`
  - Claude skill `camofox-browser` with `fetch.py` one-shot script (URL → a11y tree on stdout)
  - Verified end-to-end: `linkedin.com/in/satyanadella` → `Satya Nadella - Chairman and CEO at Microsoft | LinkedIn` (HTTP 999 bypassed)

### System requirements (new for v2.0)

- **Camofox is opt-in** — geniriclaw runs fine without it. To enable:
  - Node.js ≥ 18 (`brew install node` on macOS)
  - ~330 MB disk for Camoufox binaries (downloaded by `npm install`)
  - macOS only in this release (Linux/systemd will be a separate release)

### Migration from v1.0-light

Existing users on v1.0-light upgrading to v2.0:
- Bot will be **silent on reboots** (was: random phrase). To opt out — pin `v1.0-light` tag.
- Tool indicator format changed (no «Инструмент |» prefix). Visual only, no breaking change in API.
- New `tasks.parallel_chat_when_busy` defaults to `False` — old sequential behavior preserved unless you flip the flag.
- New `geniriclaw camofox` subcommand exists but does nothing until you run `geniriclaw camofox install`. Existing pipx installs see no change in disk size.

### How to install

```bash
# Latest (v2.0) from this fork
pipx install git+https://github.com/omniokimi/geniriclaw.git@v2.0.0

# Or pin to v1.0 light edition (no AI greeting, no parallel chat, no Camofox)
pipx install git+https://github.com/omniokimi/geniriclaw.git@v1.0-light
```

---

## [1.0-light] — 2026-04-26 — Light Edition (epoch baseline)

Snapshot of the omniokimi fork before the v2 expansion. Includes upstream igorfabrus/geniriclaw 0.15.0 with these fork-specific patches:

- **CLAUDE_MODELS_ORDERED** with `claude-opus-4-7[1m]` 1M-context variant added
- **OpenRouter integration** for image generation (Gemini Image / Nano Banana — replaces GRSAI)
- **Random startup phrases** (Russian) replacing the static "Bot Started — ready to go"
- **Drop redundant Bot Started header** — only the random phrase is sent (no banner)
- `INSTALL_NEW_MAC.md` — comprehensive deployment guide

Use this version if you want a lean install without browser dependencies (Node.js + Camoufox ~330MB) and prefer the simpler reboot notification behaviour.

```bash
pipx install git+https://github.com/omniokimi/geniriclaw.git@v1.0-light
```
