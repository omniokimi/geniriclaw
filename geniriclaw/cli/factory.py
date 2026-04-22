"""CLI backend factory -- returns the right provider based on config."""

from __future__ import annotations

import logging

from geniriclaw.cli.base import BaseCLI, CLIConfig

logger = logging.getLogger(__name__)


def create_cli(config: CLIConfig) -> BaseCLI:
    """Create a CLI backend instance based on ``config.provider``."""
    logger.debug("CLI factory creating provider=%s", config.provider)
    if config.provider == "gemini":
        from geniriclaw.cli.gemini_provider import GeminiCLI

        return GeminiCLI(config)

    if config.provider == "codex":
        from geniriclaw.cli.codex_provider import CodexCLI

        return CodexCLI(config)

    from geniriclaw.cli.claude_provider import ClaudeCodeCLI

    return ClaudeCodeCLI(config)
