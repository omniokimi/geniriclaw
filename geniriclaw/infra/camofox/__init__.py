"""Camofox-browser integration: anti-detection real browser as a managed
local service inside geniriclaw.

Public surface:

- ``CamofoxClient`` — Python HTTP client for the Camofox REST API.
- ``CamofoxUnavailable`` / ``CamofoxError`` — typed exceptions.
- ``DEFAULT_URL`` — ``http://127.0.0.1:9377``.

Server lifecycle is managed by ``geniriclaw camofox install/start/stop/status``
(see ``geniriclaw.cli.camofox_commands``); this package only contains the
client and installer logic.
"""

from geniriclaw.infra.camofox.client import (
    DEFAULT_URL,
    CamofoxClient,
    CamofoxError,
    CamofoxUnavailable,
)

__all__ = [
    "DEFAULT_URL",
    "CamofoxClient",
    "CamofoxError",
    "CamofoxUnavailable",
]
