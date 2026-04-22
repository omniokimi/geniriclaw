"""Status display CLI commands (``geniriclaw status``, ``geniriclaw help``)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from geniriclaw.i18n import t_rich
from geniriclaw.infra.platform import is_windows
from geniriclaw.workspace.paths import GeniriclawPaths, resolve_paths

_console = Console()


@dataclass(slots=True)
class StatusSummary:
    """Runtime status inputs needed by the status panel renderer."""

    bot_running: bool
    bot_pid: int | None
    bot_uptime: str
    provider: str
    model: str
    docker_enabled: bool
    docker_name: str | None
    error_count: int


def build_status_lines(status: StatusSummary, *, paths: GeniriclawPaths) -> list[str]:
    """Assemble the status panel content lines."""
    lines: list[str] = []
    if status.bot_running:
        lines.append(t_rich("status.running", pid=status.bot_pid, uptime=status.bot_uptime))
    else:
        lines.append(t_rich("status.not_running"))
    lines.append(t_rich("status.provider", provider=status.provider, model=status.model))
    if status.docker_enabled:
        lines.append(t_rich("status.docker_enabled", name=status.docker_name))
    else:
        lines.append(t_rich("status.docker_disabled"))
    if status.error_count > 0:
        lines.append(t_rich("status.errors_found", count=status.error_count))
    else:
        lines.append(t_rich("status.errors_none"))
    lines.append("")
    lines.append(t_rich("status.paths_header"))
    lines.append(f"  Home:       [cyan]{paths.geniriclaw_home}[/cyan]")
    lines.append(f"  Config:     [cyan]{paths.config_path}[/cyan]")
    lines.append(f"  Workspace:  [cyan]{paths.workspace}[/cyan]")
    lines.append(f"  Logs:       [cyan]{paths.logs_dir}[/cyan]")
    lines.append(f"  Sessions:   [cyan]{paths.sessions_path}[/cyan]")
    return lines


def count_log_errors(log_dir: Path) -> int:
    """Count ERROR entries in the most recent log file."""
    if not log_dir.is_dir():
        return 0
    log_files = sorted(
        log_dir.glob("geniriclaw*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not log_files:
        return 0
    try:
        return log_files[0].read_text(encoding="utf-8", errors="replace").count(" ERROR ")
    except OSError:
        return 0


def print_status() -> None:
    """Print bot status, paths, and runtime info including sub-agents."""
    from geniriclaw.cli_commands.agents import load_agents_registry, print_agents_status

    paths = resolve_paths()
    try:
        data: dict[str, object] = json.loads(
            paths.config_path.read_text(encoding="utf-8"),
        )
    except (json.JSONDecodeError, OSError):
        return

    provider = data.get("provider", "claude")
    model = data.get("model", "opus")
    docker_cfg = data.get("docker", {})
    docker_enabled = isinstance(docker_cfg, dict) and bool(docker_cfg.get("enabled"))
    docker_name: str | None = None
    if docker_enabled and isinstance(docker_cfg, dict):
        docker_name = str(docker_cfg.get("container_name", "geniriclaw-sandbox"))

    # Running state
    pid_file = paths.geniriclaw_home / "bot.pid"
    bot_running = False
    bot_pid: int | None = None
    bot_uptime = ""
    if pid_file.exists():
        try:
            bot_pid = int(pid_file.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            bot_pid = None
        if bot_pid is not None:
            from geniriclaw.infra.pidlock import _is_process_alive

            bot_running = _is_process_alive(bot_pid)
            if bot_running:
                mtime = datetime.fromtimestamp(pid_file.stat().st_mtime, tz=UTC)
                delta = datetime.now(UTC) - mtime
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                bot_uptime = f"{hours}h {minutes}m"

    # Error count from latest log
    error_count = count_log_errors(paths.logs_dir)

    # Build status lines
    summary = StatusSummary(
        bot_running=bot_running,
        bot_pid=bot_pid,
        bot_uptime=bot_uptime,
        provider=str(provider),
        model=str(model),
        docker_enabled=docker_enabled,
        docker_name=str(docker_name) if docker_name else None,
        error_count=error_count,
    )
    lines = build_status_lines(summary, paths=paths)

    _console.print(
        Panel(
            "\n".join(lines),
            title="[bold]Status — main[/bold]",
            border_style="green",
            padding=(1, 2),
        ),
    )

    # Show sub-agents
    agents = load_agents_registry(paths)
    if agents:
        print_agents_status(agents, bot_running=bot_running)


def print_usage() -> None:
    """Print commands and smart status information."""
    from geniriclaw.__main__ import _is_configured

    _console.print()
    banner_path = Path(__file__).resolve().parent.parent / "_banner.txt"
    try:
        banner_text = banner_path.read_text(encoding="utf-8").rstrip()
    except OSError:
        banner_text = "geniriclaw.dev"
    _console.print(
        Panel(
            Text(banner_text, style="bold cyan"),
            subtitle=f"[dim]{t_rich('wizard.common.subtitle')}[/dim]",
            border_style="cyan",
            padding=(0, 2),
        ),
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold green", min_width=24)
    table.add_column()
    table.add_row("geniriclaw", t_rich("help.geniriclaw"))
    table.add_row("geniriclaw onboarding", t_rich("help.onboarding"))
    table.add_row("geniriclaw stop", t_rich("help.stop"))
    table.add_row("geniriclaw restart", t_rich("help.restart"))
    table.add_row("geniriclaw reset", t_rich("help.reset"))
    table.add_row("geniriclaw upgrade", t_rich("help.upgrade"))
    table.add_row("geniriclaw uninstall", t_rich("help.uninstall"))
    is_macos = sys.platform == "darwin"
    svc_hint = "Task Scheduler" if is_windows() else ("launchd" if is_macos else "systemd")
    table.add_row("geniriclaw service install", t_rich("help.service_install", hint=svc_hint))
    table.add_row("geniriclaw service", t_rich("help.service"))
    table.add_row("geniriclaw agents", t_rich("help.agents"))
    table.add_row("geniriclaw docker", t_rich("help.docker"))
    table.add_row("geniriclaw api", t_rich("help.api"))
    table.add_row("geniriclaw install <extra>", t_rich("help.install"))
    table.add_row("geniriclaw status", t_rich("help.status"))
    table.add_row("geniriclaw help", t_rich("help.help"))
    table.add_row("-v, --verbose", t_rich("help.verbose"))

    _console.print(
        Panel(table, title="[bold]Commands[/bold]", border_style="blue", padding=(1, 0)),
    )

    if _is_configured():
        print_status()
    else:
        _console.print(
            Panel(
                t_rich("status.not_configured"),
                title="[bold]Status[/bold]",
                border_style="yellow",
                padding=(1, 2),
            ),
        )
    _console.print()
