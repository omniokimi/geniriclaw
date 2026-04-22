"""Tests for the exception hierarchy."""

from geniriclaw.errors import (
    CLIError,
    GeniriclawError,
    PathValidationError,
    SecurityError,
    WorkspaceError,
)


def test_base_error_is_exception() -> None:
    assert issubclass(GeniriclawError, Exception)


def test_cli_error_inherits_base() -> None:
    err = CLIError("cli broke")
    assert isinstance(err, GeniriclawError)
    assert str(err) == "cli broke"


def test_workspace_error_inherits_base() -> None:
    assert isinstance(WorkspaceError("no workspace"), GeniriclawError)


def test_security_error_inherits_base() -> None:
    assert isinstance(SecurityError("blocked"), GeniriclawError)


def test_path_validation_error_inherits_security() -> None:
    err = PathValidationError("outside root")
    assert isinstance(err, SecurityError)
    assert isinstance(err, GeniriclawError)


def test_catch_all_with_base() -> None:
    """All subclasses catchable via GeniriclawError."""
    for cls in (CLIError, WorkspaceError, SecurityError, PathValidationError):
        try:
            raise cls("test")
        except GeniriclawError:
            pass
