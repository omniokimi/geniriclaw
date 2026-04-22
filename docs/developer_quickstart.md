# Developer Quickstart

Fast onboarding path for contributors and junior devs.

## 1) Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional for full runtime validation:

- install/auth at least one provider CLI (`claude`, `codex`, `gemini`)
- set up a messaging transport:
  - **Telegram**: bot token from @BotFather + user ID (`allowed_user_ids`)
  - **Matrix**: account on any homeserver (homeserver URL, user ID, password, `allowed_users`)
- for Telegram group support, also set `allowed_group_ids`

## 2) Run the bot

```bash
geniriclaw
```

First run starts onboarding and writes config to `~/.geniriclaw/config/config.json`.

Primary runtime files/directories:

- `~/.geniriclaw/sessions.json`
- `~/.geniriclaw/named_sessions.json`
- `~/.geniriclaw/tasks.json`
- `~/.geniriclaw/chat_activity.json`
- `~/.geniriclaw/cron_jobs.json`
- `~/.geniriclaw/webhooks.json`
- `~/.geniriclaw/startup_state.json`
- `~/.geniriclaw/inflight_turns.json`
- `~/.geniriclaw/SHAREDMEMORY.md`
- `~/.geniriclaw/agents.json`
- `~/.geniriclaw/agents/`
- `~/.geniriclaw/workspace/`
- `~/.geniriclaw/logs/agent.log`

## 3) Quality gates

```bash
pytest
ruff format .
ruff check .
mypy geniriclaw
```

Expected: zero warnings, zero errors.

## 4) Core mental model

```text
Telegram / Matrix / API input
  -> ingress layer (TelegramBot / MatrixBot / ApiServer)
  -> orchestrator flow
  -> provider CLI subprocess
  -> response delivery (transport-specific)

background/async results
  -> Envelope adapters
  -> MessageBus
  -> optional session injection
  -> transport delivery (Telegram or Matrix)
```

## 5) Read order in code

Entry + command layer:

- `geniriclaw/__main__.py`
- `geniriclaw/cli_commands/`

Runtime hot path:

- `geniriclaw/multiagent/supervisor.py`
- `geniriclaw/messenger/telegram/app.py`
- `geniriclaw/messenger/telegram/startup.py`
- `geniriclaw/orchestrator/core.py`
- `geniriclaw/orchestrator/lifecycle.py`
- `geniriclaw/orchestrator/flows.py`

Delivery/task/session core:

- `geniriclaw/bus/`
- `geniriclaw/session/manager.py`
- `geniriclaw/tasks/hub.py`
- `geniriclaw/tasks/registry.py`

Provider/API/workspace core:

- `geniriclaw/cli/service.py` + provider wrappers
- `geniriclaw/api/server.py`
- `geniriclaw/workspace/init.py`
- `geniriclaw/workspace/rules_selector.py`
- `geniriclaw/workspace/skill_sync.py`

## 6) Common debug paths

If command behavior is wrong:

1. `geniriclaw/__main__.py`
2. `geniriclaw/cli_commands/*`

If Telegram routing is wrong:

1. `geniriclaw/messenger/telegram/middleware.py`
2. `geniriclaw/messenger/telegram/app.py`
3. `geniriclaw/orchestrator/commands.py`
4. `geniriclaw/orchestrator/flows.py`

If Matrix routing is wrong:

1. `geniriclaw/messenger/matrix/bot.py`
2. `geniriclaw/messenger/matrix/transport.py`
3. `geniriclaw/orchestrator/flows.py`

If background results look wrong:

1. `geniriclaw/bus/adapters.py`
2. `geniriclaw/bus/bus.py`
3. `geniriclaw/messenger/telegram/transport.py` (or `geniriclaw/messenger/matrix/transport.py`)

If tasks are wrong:

1. `geniriclaw/tasks/hub.py`
2. `geniriclaw/tasks/registry.py`
3. `geniriclaw/multiagent/internal_api.py`
4. `geniriclaw/_home_defaults/workspace/tools/task_tools/*.py`

If API is wrong:

1. `geniriclaw/api/server.py`
2. `geniriclaw/orchestrator/lifecycle.py` (API startup wiring)
3. `geniriclaw/files/*` (allowed roots, MIME, prompt building)

## 7) Behavior details to remember

- `/stop` and `/stop_all` are pre-routing abort paths in middleware/bot.
- `/new` resets only active provider bucket for the active `SessionKey`.
- session identity is transport-aware: `SessionKey(transport, chat_id, topic_id)`.
- `/model` inside a topic updates only that topic session (not global config).
- task tools now support permanent single-task removal via `delete_task.py` (`/tasks/delete`).
- task routing is topic-aware via `thread_id` and `GENIRICLAW_TOPIC_ID`.
- API auth accepts optional `channel_id` for per-channel session isolation.
- startup recovery uses `inflight_turns.json` + recovered named sessions.
- auth allowlists (`allowed_user_ids`, `allowed_group_ids`) are hot-reloadable.
- `geniriclaw agents add` is a Telegram-focused scaffold; Matrix sub-agents are supported through `agents.json` or the bundled agent tool scripts.

Continue with `docs/system_overview.md` and `docs/architecture.md` for complete runtime detail.
