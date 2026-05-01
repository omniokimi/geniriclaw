"""Camofox-browser installer: bootstrap a local Camofox service on macOS.

Public entry points (called from ``geniriclaw camofox <command>``):
- ``install()`` — clone + npm install + render plist + launchctl bootstrap.
- ``start()`` / ``stop()`` / ``restart()`` — wrap launchctl.
- ``status()`` — return a structured snapshot of the install / runtime.
- ``uninstall()`` — bootout + remove plist (keeps data).

This module is macOS-first; Linux support stubs out with a clear error.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

logger_name = "geniriclaw.infra.camofox.installer"

CAMOFOX_REPO = "https://github.com/jo-inc/camofox-browser.git"
PLIST_LABEL = "dev.geniri.camofox"
DEFAULT_PORT = 9377


@dataclass(slots=True)
class InstallPaths:
    """Resolved filesystem paths for a Camofox installation under HOME."""

    home: Path
    base: Path                # ~/.geniriclaw/camofox
    repo: Path                # ~/.geniriclaw/camofox/camofox-browser
    logs: Path                # ~/.geniriclaw/camofox/logs
    plist: Path               # ~/Library/LaunchAgents/dev.geniri.camofox.plist

    @classmethod
    def resolve(cls, home: Path | None = None) -> InstallPaths:
        h = home or Path.home()
        base = h / ".geniriclaw" / "camofox"
        return cls(
            home=h,
            base=base,
            repo=base / "camofox-browser",
            logs=base / "logs",
            plist=h / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist",
        )


class InstallerError(RuntimeError):
    """User-visible installer failure with a (hopefully) actionable message."""


# -- prerequisites ----------------------------------------------------------

# Standard Homebrew bin locations on macOS (Intel + Apple Silicon).
# pipx-launched Python often inherits a stripped PATH that lacks these,
# so we add them explicitly before resolving ``node`` / ``npm`` / ``git``.
_EXTRA_PATH_DIRS = ("/usr/local/bin", "/opt/homebrew/bin", "/usr/bin", "/bin")


def _which(binary: str) -> str | None:
    found = shutil.which(binary)
    if found:
        return found
    for d in _EXTRA_PATH_DIRS:
        candidate = Path(d) / binary
        if candidate.is_file():
            return str(candidate)
    return None


def _check_macos() -> None:
    if sys.platform != "darwin":
        raise InstallerError(
            f"Camofox installer currently supports macOS only (detected: {sys.platform}). "
            "On Linux, run camofox-browser manually under systemd."
        )


def _check_node() -> str:
    node = _which("node")
    if not node:
        raise InstallerError(
            "Node.js is required but not found in PATH. "
            "Install with: brew install node"
        )
    return node


def _check_git() -> str:
    git = _which("git")
    if not git:
        raise InstallerError("git is required but not found in PATH.")
    return git


# -- core operations --------------------------------------------------------

def install(*, paths: InstallPaths | None = None, force_reclone: bool = False) -> InstallPaths:
    """Clone the upstream repo, run npm install, deploy the LaunchAgent.

    Idempotent: re-running on an existing install only refreshes deps and
    reloads launchd. Pass ``force_reclone=True`` to wipe the repo first.
    """
    _check_macos()
    node = _check_node()
    git = _check_git()
    p = paths or InstallPaths.resolve()
    p.base.mkdir(parents=True, exist_ok=True)
    p.logs.mkdir(parents=True, exist_ok=True)

    if force_reclone and p.repo.exists():
        shutil.rmtree(p.repo)

    if not p.repo.exists():
        subprocess.run(
            [git, "clone", "--depth", "1", CAMOFOX_REPO, str(p.repo)],
            check=True,
        )
    else:
        # Fast-forward to latest main; if remote diverged, leave the user a hint.
        subprocess.run([git, "-C", str(p.repo), "fetch", "--depth", "1", "origin", "main"],
                       check=False)
        subprocess.run([git, "-C", str(p.repo), "reset", "--hard", "origin/main"],
                       check=False)

    npm = _which("npm") or str(Path(node).parent / "npm")
    env = os.environ.copy()
    # Make sure npm doesn't sneak in a different binary via PATH oddities.
    env["PATH"] = f"{Path(node).parent}:{env.get('PATH', '')}"
    subprocess.run([npm, "install"], cwd=p.repo, check=True, env=env)

    plist_xml = _render_plist(node=node, home=p.home)
    p.plist.parent.mkdir(parents=True, exist_ok=True)
    p.plist.write_text(plist_xml, encoding="utf-8")

    _launchctl_bootout_quiet(p.plist)
    _launchctl_bootstrap(p.plist)
    return p


def uninstall(*, paths: InstallPaths | None = None, purge_data: bool = False) -> None:
    """Stop the LaunchAgent and remove the plist.

    By default ``~/.geniriclaw/camofox/`` (the data dir) is kept; pass
    ``purge_data=True`` to remove it as well.
    """
    p = paths or InstallPaths.resolve()
    _launchctl_bootout_quiet(p.plist)
    if p.plist.exists():
        p.plist.unlink()
    if purge_data and p.base.exists():
        shutil.rmtree(p.base)


def start(*, paths: InstallPaths | None = None) -> None:
    p = paths or InstallPaths.resolve()
    if not p.plist.exists():
        raise InstallerError("LaunchAgent plist missing. Run `geniriclaw camofox install` first.")
    _launchctl_bootstrap(p.plist)


def stop(*, paths: InstallPaths | None = None) -> None:
    p = paths or InstallPaths.resolve()
    _launchctl_bootout_quiet(p.plist)


def restart(*, paths: InstallPaths | None = None) -> None:
    p = paths or InstallPaths.resolve()
    if not p.plist.exists():
        raise InstallerError("LaunchAgent plist missing. Run `geniriclaw camofox install` first.")
    subprocess.run(
        ["launchctl", "kickstart", "-k", _user_domain_target(p.plist)],
        check=False,
    )


# -- status -----------------------------------------------------------------

@dataclass(slots=True)
class CamofoxStatus:
    installed: bool
    plist_loaded: bool
    pid: int | None
    health_ok: bool
    health_payload: dict | None
    repo_path: Path
    plist_path: Path
    error: str | None = None

    def summary(self) -> str:
        if not self.installed:
            return "⛔ not installed (run `geniriclaw camofox install`)"
        if not self.plist_loaded:
            return "⚠️ installed but LaunchAgent not loaded (run `geniriclaw camofox start`)"
        if not self.health_ok:
            return f"⚠️ loaded but /health unreachable (pid={self.pid}, error={self.error})"
        mem = (self.health_payload or {}).get("memory", {}).get("rssMb", "?")
        return f"✅ running on :{DEFAULT_PORT} (pid={self.pid}, RSS={mem}MB)"


def status(*, paths: InstallPaths | None = None) -> CamofoxStatus:
    p = paths or InstallPaths.resolve()
    installed = p.repo.exists() and (p.repo / "server.js").exists()
    plist_loaded, pid = _launchctl_pid(p.plist)
    health_payload = None
    health_ok = False
    error: str | None = None
    if plist_loaded:
        try:
            resp = httpx.get(f"http://127.0.0.1:{DEFAULT_PORT}/health", timeout=3.0)
            if resp.status_code == 200:
                health_payload = resp.json()
                health_ok = bool(health_payload.get("ok"))
            else:
                error = f"HTTP {resp.status_code}"
        except httpx.HTTPError as e:
            error = str(e)
    return CamofoxStatus(
        installed=installed,
        plist_loaded=plist_loaded,
        pid=pid,
        health_ok=health_ok,
        health_payload=health_payload,
        repo_path=p.repo,
        plist_path=p.plist,
        error=error,
    )


# -- launchctl plumbing -----------------------------------------------------

def _render_plist(*, node: str, home: Path) -> str:
    template_path = (
        Path(__file__).resolve().parent.parent.parent
        / "_home_defaults"
        / "launchd"
        / "dev.geniri.camofox.plist.template"
    )
    raw = template_path.read_text(encoding="utf-8")
    return raw.replace("{{NODE_BIN}}", node).replace("{{HOME}}", str(home))


def _user_domain_target(plist_path: Path) -> str:
    return f"gui/{os.getuid()}/{plist_path.stem}"


def _launchctl_bootout_quiet(plist_path: Path) -> None:
    subprocess.run(
        ["launchctl", "bootout", _user_domain_target(plist_path)],
        check=False,
        capture_output=True,
    )


def _launchctl_bootstrap(plist_path: Path) -> None:
    subprocess.run(
        ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist_path)],
        check=False,
    )


def _launchctl_pid(plist_path: Path) -> tuple[bool, int | None]:
    """Return (loaded, pid) by parsing `launchctl list | grep <label>`."""
    label = plist_path.stem
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[2].strip() == label:
            pid_str = parts[0].strip()
            try:
                pid = int(pid_str) if pid_str != "-" else None
            except ValueError:
                pid = None
            return True, pid
    return False, None
