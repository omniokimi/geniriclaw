"""Webhook system: HTTP ingress for external event triggers."""

from geniriclaw.webhook.manager import WebhookManager
from geniriclaw.webhook.models import WebhookEntry, WebhookResult

__all__ = ["WebhookEntry", "WebhookManager", "WebhookResult"]
