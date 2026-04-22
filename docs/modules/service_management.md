# service_management

Platform-specific background service management for `geniriclaw service ...`.

## Dispatch model

`geniriclaw/infra/service.py` is the single dispatcher:

- Linux -> `service_linux.py`
- macOS -> `service_macos.py`
- Windows -> `service_windows.py`

Every backend exposes the same surface:

- `is_service_available()`
- `is_service_installed()`
- `is_service_running()`
- `install_service()`
- `start_service()`
- `stop_service()`
- `uninstall_service()`
- `print_service_status()`
- `print_service_logs()`

This keeps `cli_commands/service.py` platform-agnostic.

## Common runtime behavior

- onboarding offers service install whenever the active platform backend is available
- `stop_bot()` stops the installed service before killing the current process tree, so the service manager does not immediately respawn it
- restart semantics still come from the process exit code (`42`) and the surrounding backend policy
- file logs live under `~/.geniriclaw/logs/`

## Linux backend

Implementation: `geniriclaw/infra/service_linux.py`

Mechanism:

- systemd user service
- unit file: `~/.config/systemd/user/geniriclaw.service`
- enable + start via `systemctl --user`

Service unit details:

- `ExecStart=<geniriclaw binary>`
- `Restart=on-failure`
- `RestartSec=5`
- sets `PATH`, `HOME`, and `GENIRICLAW_SUPERVISOR=1`
- `WantedBy=default.target`

Operational notes:

- installer attempts `sudo loginctl enable-linger <user>` when linger is missing
- without linger, the user service may stop after logout
- `geniriclaw service logs` follows `journalctl --user -u geniriclaw -f --no-hostname`

## macOS backend

Implementation: `geniriclaw/infra/service_macos.py`

Mechanism:

- launchd Launch Agent
- plist: `~/Library/LaunchAgents/dev.geniri.claw.plist`
- loaded via `launchctl load -w`

Launch Agent details:

- `RunAtLoad=true`
- `KeepAlive.SuccessfulExit=false` so restart happens on crash, not clean exit
- `ThrottleInterval=10`
- `ProcessType=Background`
- extends `PATH` with common system paths plus discovered NVM bin directories
- sets `HOME` and `GENIRICLAW_SUPERVISOR=1`
- stdout/stderr go to `~/.geniriclaw/logs/service.log` and `service.err`

Operational notes:

- `geniriclaw service logs` tails file logs from `~/.geniriclaw/logs/` rather than using `launchctl`
- status uses `launchctl list dev.geniri.claw`

## Windows backend

Implementation: `geniriclaw/infra/service_windows.py`

Mechanism:

- Task Scheduler task named `geniriclaw`
- created through `schtasks.exe` with an XML definition

Task details:

- starts 10 seconds after user logon
- restart-on-failure enabled: 3 retries, 1 minute apart
- runs with `InteractiveToken` and `LeastPrivilege`
- prefers `pythonw.exe -m geniriclaw` for windowless execution
- falls back to the `geniriclaw` binary when `pythonw.exe` is unavailable

Operational notes:

- some systems require an elevated terminal for task creation/removal; backend detects common access-denied variants and shows an admin hint panel
- `geniriclaw service logs` tails file logs from `~/.geniriclaw/logs/`
- the backend writes a temporary XML file under `~/.geniriclaw/geniriclaw_task.xml` during install and removes it after task creation

## Why junior devs should care

If service behavior looks wrong, the first question is not "is the bot broken?" but "which backend owns this process?"

- Linux issues usually mean systemd user-service state or missing linger
- macOS issues usually mean Launch Agent load state or PATH resolution
- Windows issues usually mean Task Scheduler permissions or `pythonw.exe` resolution

For CLI routing see `docs/modules/cli_commands.md`. For low-level infra context see `docs/modules/infra.md`.
