"""Messenger abstraction layer — transport-agnostic protocols and registry."""

from geniriclaw.messenger.capabilities import MessengerCapabilities
from geniriclaw.messenger.commands import (
    DIRECT_COMMANDS,
    MULTIAGENT_COMMANDS,
    ORCHESTRATOR_COMMANDS,
    classify_command,
)
from geniriclaw.messenger.multi import MultiBotAdapter
from geniriclaw.messenger.notifications import CompositeNotificationService, NotificationService
from geniriclaw.messenger.protocol import BotProtocol
from geniriclaw.messenger.registry import create_bot
from geniriclaw.messenger.send_opts import BaseSendOpts

__all__ = [
    "DIRECT_COMMANDS",
    "MULTIAGENT_COMMANDS",
    "ORCHESTRATOR_COMMANDS",
    "BaseSendOpts",
    "BotProtocol",
    "CompositeNotificationService",
    "MessengerCapabilities",
    "MultiBotAdapter",
    "NotificationService",
    "classify_command",
    "create_bot",
]
