"""Project-level exception hierarchy."""


class GeniriclawError(Exception):
    """Base for all geniriclaw exceptions."""


class CLIError(GeniriclawError):
    """CLI execution failed."""


class WorkspaceError(GeniriclawError):
    """Workspace initialization or access failed."""


class SessionError(GeniriclawError):
    """Session persistence or lifecycle failed."""


class CronError(GeniriclawError):
    """Cron job scheduling or execution failed."""


class StreamError(GeniriclawError):
    """Streaming output failed."""


class SecurityError(GeniriclawError):
    """Security violation detected."""


class PathValidationError(SecurityError):
    """File path failed validation."""


class WebhookError(GeniriclawError):
    """Webhook server or dispatch failed."""
