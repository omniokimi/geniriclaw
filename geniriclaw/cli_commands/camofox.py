"""``geniriclaw camofox <subcommand>`` — manage the local Camofox-browser service.

Subcommands:
- ``install``    — clone repo, npm install, deploy LaunchAgent.
- ``start``      — bootstrap LaunchAgent (idempotent).
- ``stop``       — bootout LaunchAgent.
- ``restart``    — kickstart -k.
- ``status``     — show install state, PID, /health.
- ``uninstall``  — bootout + remove plist (data preserved by default).
"""

from __future__ import annotations

import sys

from rich.console import Console

from geniriclaw.infra.camofox import installer as cf

_console = Console()


def _print_status(s: cf.CamofoxStatus) -> None:
    _console.print(f"[bold]Camofox:[/bold] {s.summary()}")
    _console.print(f"  repo:  {s.repo_path}")
    _console.print(f"  plist: {s.plist_path}")
    if s.health_payload:
        mem = s.health_payload.get("memory", {})
        _console.print(
            f"  tabs={s.health_payload.get('activeTabs', 0)} "
            f"sessions={s.health_payload.get('activeSessions', 0)} "
            f"RSS={mem.get('rssMb', '?')}MB"
        )


def cmd_camofox(args: list[str]) -> None:
    """Dispatch ``geniriclaw camofox <sub>`` to the installer module."""
    sub_args = [a for a in args if not a.startswith("-")]
    if "camofox" in sub_args:
        sub_args = sub_args[sub_args.index("camofox") + 1:]
    sub = sub_args[0] if sub_args else "status"
    force_reclone = "--force" in args or "--reclone" in args

    try:
        if sub == "install":
            _console.print("[cyan]Installing Camofox-browser… (this may take 5–10 min)[/cyan]")
            cf.install(force_reclone=force_reclone)
            _print_status(cf.status())
        elif sub == "uninstall":
            purge = "--purge" in args
            cf.uninstall(purge_data=purge)
            _console.print("[green]Camofox uninstalled.[/green]")
        elif sub == "start":
            cf.start()
            _print_status(cf.status())
        elif sub == "stop":
            cf.stop()
            _console.print("[yellow]Camofox stopped.[/yellow]")
        elif sub == "restart":
            cf.restart()
            _print_status(cf.status())
        elif sub == "status":
            _print_status(cf.status())
        else:
            _console.print(f"[red]Unknown subcommand:[/red] {sub}")
            _console.print("Available: install / start / stop / restart / status / uninstall")
            sys.exit(2)
    except cf.InstallerError as e:
        _console.print(f"[red]{e}[/red]")
        sys.exit(1)
