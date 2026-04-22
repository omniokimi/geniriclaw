"""CLI layer: provider abstraction, process tracking, streaming."""

from geniriclaw.cli.auth import AuthResult as AuthResult
from geniriclaw.cli.auth import AuthStatus as AuthStatus
from geniriclaw.cli.auth import check_all_auth as check_all_auth
from geniriclaw.cli.base import BaseCLI as BaseCLI
from geniriclaw.cli.base import CLIConfig as CLIConfig
from geniriclaw.cli.coalescer import CoalesceConfig as CoalesceConfig
from geniriclaw.cli.coalescer import StreamCoalescer as StreamCoalescer
from geniriclaw.cli.factory import create_cli as create_cli
from geniriclaw.cli.process_registry import ProcessRegistry as ProcessRegistry
from geniriclaw.cli.service import CLIService as CLIService
from geniriclaw.cli.service import CLIServiceConfig as CLIServiceConfig
from geniriclaw.cli.types import AgentRequest as AgentRequest
from geniriclaw.cli.types import AgentResponse as AgentResponse
from geniriclaw.cli.types import CLIResponse as CLIResponse

__all__ = [
    "AgentRequest",
    "AgentResponse",
    "AuthResult",
    "AuthStatus",
    "BaseCLI",
    "CLIConfig",
    "CLIResponse",
    "CLIService",
    "CLIServiceConfig",
    "CoalesceConfig",
    "ProcessRegistry",
    "StreamCoalescer",
    "check_all_auth",
    "create_cli",
]
