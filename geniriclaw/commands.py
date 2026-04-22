"""Bot command definitions shared across layers.

Commands are ordered by usage frequency (most used first).
Descriptions are kept ≤22 chars so mobile clients don't truncate.
"""

from __future__ import annotations

from geniriclaw.i18n import t_cmd

# -- Core commands (every agent, shown in Telegram popup) ------------------
# Sorted by typical usage: daily actions → power-user → rare maintenance.


def get_bot_commands() -> list[tuple[str, str]]:
    """Return bot commands with translated descriptions."""
    return [
        # Daily
        ("new", t_cmd("bot.new")),
        ("stop", t_cmd("bot.stop")),
        ("interrupt", t_cmd("bot.interrupt")),
        ("model", t_cmd("bot.model")),
        # Info
        ("help", t_cmd("bot.help")),
        # Maintenance
        ("diagnose", t_cmd("bot.diagnose")),
        ("restart", t_cmd("bot.restart")),
    ]


def get_multiagent_sub_commands() -> list[tuple[str, str]]:
    """Return multi-agent sub-commands with translated descriptions."""
    return [
        ("stop_all", t_cmd("multiagent.stop_all")),
    ]


# Backward-compatible module-level aliases.
# These are evaluated at import time, so i18n must be auto-initialized by then.
BOT_COMMANDS: list[tuple[str, str]] = get_bot_commands()
MULTIAGENT_SUB_COMMANDS: list[tuple[str, str]] = get_multiagent_sub_commands()
