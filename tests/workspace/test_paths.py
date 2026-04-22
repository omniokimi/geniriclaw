"""Tests for GeniriclawPaths and resolve_paths."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from geniriclaw.workspace.paths import GeniriclawPaths, resolve_paths


def test_workspace_property() -> None:
    paths = GeniriclawPaths(
        geniriclaw_home=Path("/home/test/.geniriclaw"),
        home_defaults=Path("/opt/geniriclaw/workspace"),
        framework_root=Path("/opt/geniriclaw"),
    )
    assert paths.workspace == Path("/home/test/.geniriclaw/workspace")


def test_config_path() -> None:
    paths = GeniriclawPaths(
        geniriclaw_home=Path("/home/test/.geniriclaw"),
        home_defaults=Path("/opt/geniriclaw/workspace"),
        framework_root=Path("/opt/geniriclaw"),
    )
    assert paths.config_path == Path("/home/test/.geniriclaw/config/config.json")


def test_sessions_path() -> None:
    paths = GeniriclawPaths(
        geniriclaw_home=Path("/home/test/.geniriclaw"),
        home_defaults=Path("/opt/geniriclaw/workspace"),
        framework_root=Path("/opt/geniriclaw"),
    )
    assert paths.sessions_path == Path("/home/test/.geniriclaw/sessions.json")


def test_logs_dir() -> None:
    paths = GeniriclawPaths(
        geniriclaw_home=Path("/home/test/.geniriclaw"),
        home_defaults=Path("/opt/geniriclaw/workspace"),
        framework_root=Path("/opt/geniriclaw"),
    )
    assert paths.logs_dir == Path("/home/test/.geniriclaw/logs")


def test_home_defaults() -> None:
    paths = GeniriclawPaths(
        geniriclaw_home=Path("/x"),
        home_defaults=Path("/opt/geniriclaw/workspace"),
        framework_root=Path("/opt/geniriclaw"),
    )
    assert paths.home_defaults == Path("/opt/geniriclaw/workspace")


def test_resolve_paths_explicit() -> None:
    paths = resolve_paths(geniriclaw_home="/tmp/test_home", framework_root="/tmp/test_fw")
    assert paths.geniriclaw_home == Path("/tmp/test_home").resolve()
    assert paths.framework_root == Path("/tmp/test_fw").resolve()


def test_resolve_paths_env_vars() -> None:
    with patch.dict(
        os.environ, {"GENIRICLAW_HOME": "/tmp/env_home", "GENIRICLAW_FRAMEWORK_ROOT": "/tmp/env_fw"}
    ):
        paths = resolve_paths()
        assert paths.geniriclaw_home == Path("/tmp/env_home").resolve()
        assert paths.framework_root == Path("/tmp/env_fw").resolve()


def test_resolve_paths_defaults() -> None:
    with patch.dict(os.environ, {}, clear=True):
        env_clean = {
            k: v for k, v in os.environ.items() if k not in ("GENIRICLAW_HOME", "GENIRICLAW_FRAMEWORK_ROOT")
        }
        with patch.dict(os.environ, env_clean, clear=True):
            paths = resolve_paths()
            assert paths.geniriclaw_home == (Path.home() / ".geniriclaw").resolve()
