# Setup Wizard and CLI Entry

Covers `geniriclaw` command behavior, onboarding flow, and lifecycle commands.

## Files

- `geniriclaw/__main__.py`: CLI dispatch + config helpers + `run_bot`
- `geniriclaw/cli_commands/lifecycle.py`: start/stop/restart/upgrade/uninstall logic
- `geniriclaw/cli_commands/status.py`: `geniriclaw status` + `geniriclaw help`
- `geniriclaw/cli_commands/service.py`: service command routing
- `geniriclaw/cli_commands/docker.py`: docker subcommands
- `geniriclaw/cli_commands/api_cmd.py`: API enable/disable commands
- `geniriclaw/cli_commands/agents.py`: sub-agent registry commands
- `geniriclaw/cli_commands/install.py`: optional extras installer (`geniriclaw install <extra>`)
- `geniriclaw/infra/docker_extras.py`: optional Docker package registry + Dockerfile generation
- `geniriclaw/cli/init_wizard.py`: onboarding + smart reset

## CLI commands

- `geniriclaw`: start bot (auto-onboarding if needed)
- `geniriclaw onboarding` / `geniriclaw reset`: onboarding flow (with smart reset when configured)
- `geniriclaw status`
- `geniriclaw stop`
- `geniriclaw restart`
- `geniriclaw upgrade`
- `geniriclaw uninstall`
- `geniriclaw service <install|status|start|stop|logs|uninstall>`
- `geniriclaw docker <rebuild|enable|disable|mount|unmount|mounts|extras|extras-add|extras-remove>`
- `geniriclaw api <enable|disable>`
- `geniriclaw agents <list|add|remove>`
- `geniriclaw install <matrix|api>`
- `geniriclaw help`

## Configuration gate

`_is_configured()` checks all active transports:

- when `transports` is set: every listed transport must pass its checker
- when `transports` is empty: falls back to single `transport`

- **Telegram** (default): valid non-placeholder `telegram_token` + non-empty `allowed_user_ids`
- **Matrix**: non-empty `homeserver` + non-empty `user_id`

`allowed_group_ids` controls group authorization but does not satisfy startup configuration alone.

## Onboarding flow (`run_onboarding`)

1. banner
2. provider install/auth check
3. disclaimer
4. **transport selection** (Telegram or Matrix)
   - After initial setup, multiple transports can run in parallel via
     the `transports` array in `config.json` (see [config.md](../config.md))
5. transport-specific credentials:
   - Telegram: bot token prompt + user ID prompt
   - Matrix: homeserver URL + bot user ID + password + allowed users
6. Docker choice
7. Docker extras selection (only when Docker enabled)
8. timezone choice
9. write merged config + initialize workspace
10. optional service install

Step 7 shows a Rich table of optional AI/ML packages grouped by category (Audio/Speech, Vision/OCR, Document Processing, Scientific/Data, ML Frameworks, Web/Browser) with descriptions and size estimates. Users select via `questionary.checkbox`. Transitive dependencies are auto-resolved.

Return semantics:

- `True` when service install was completed
- `False` otherwise

Caller behavior:

- default `geniriclaw`: onboarding if needed, then foreground start unless service install path returned `True`
- `geniriclaw onboarding/reset`: calls `stop_bot()` first, then onboarding, then same service/foreground logic

## Lifecycle command behavior

### `stop_bot()`

Shutdown sequence:

1. stop installed service (prevents auto-respawn)
2. kill PID-file instance
3. kill remaining geniriclaw processes
4. short lock-release wait on Windows
5. stop Docker container when enabled

### Restart

- `cmd_restart()` = `stop_bot()` + process re-exec
- restart code `42` is used for service-managed restart semantics

### Upgrade

- dev installs: no self-upgrade, show guidance
- upgradeable installs: stop -> upgrade pipeline -> verify version -> restart

### Uninstall

- stop bot/service
- optional Docker image cleanup
- remove `~/.geniriclaw` via robust filesystem helper
- uninstall package (`pipx` or `pip`)

## Status panel

`geniriclaw status` shows:

- running state/PID/uptime
- provider/model
- Docker state
- error count from newest `geniriclaw*.log`
- key paths
- sub-agent status table when configured (live health if bot is running)

Note: runtime primary log file is `~/.geniriclaw/logs/agent.log`; status error counter is currently `geniriclaw*.log`-based.

## Docker command notes

`geniriclaw docker ...` commands update `config.json` and/or container/image state.

- mount/unmount paths are resolved and validated
- mount list shows host path, container target, status
- restart/rebuild is required for mount flag changes to affect running container

### Docker extras management

- `geniriclaw docker extras` shows a table of all available optional packages with their status (selected / —) and a hint to rebuild after changes.
- `geniriclaw docker extras-add <id>` adds an extra (+ transitive dependencies) to `config.json`.
- `geniriclaw docker extras-remove <id>` removes an extra from `config.json`, warns about reverse dependencies.
- without `<id>`, `extras-add` / `extras-remove` list available choices.
- after add/remove, the user must run `geniriclaw docker rebuild` to apply changes to the Docker image.
- selected extras are compiled into additional `RUN` blocks appended to the base `Dockerfile.sandbox` at build time.

## API command notes

`geniriclaw api enable`:

- requires PyNaCl
- writes/updates `config.api`
- generates token when missing

`geniriclaw api disable`:

- sets `config.api.enabled=false` (keeps token/settings)

Both require bot restart to apply.

## Service command routing

`geniriclaw service ...` delegates to platform backends:

- Linux: systemd user service
- macOS: launchd Launch Agent
- Windows: Task Scheduler

Detailed backend behavior: [service_management](service_management.md)

`geniriclaw service logs`:

- Linux: `journalctl --user -u geniriclaw -f`
- macOS/Windows: tail from `~/.geniriclaw/logs/agent.log` (fallback newest `*.log`)
