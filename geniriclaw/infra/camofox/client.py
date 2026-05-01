"""HTTP client for a locally-running Camofox-browser server.

Camofox-browser (https://github.com/jo-inc/camofox-browser) is a Node.js
service that wraps Camoufox — a Firefox fork with C++ fingerprint stealth.
It exposes a REST API on ``localhost:9377`` (by default) and is managed
by geniriclaw as a local LaunchAgent.

This client wraps the REST API in idiomatic Python and is the single
integration point used by:
- ``_home_defaults/workspace/skills/camofox-browser/fetch.py`` (Claude skill)
- ``geniriclaw camofox status`` (CLI)
- ``geniriclaw status`` (system health-check)

Connection model: one client = one persistent browser session (userId+tab).
Calling ``navigate()`` lazily provisions both. Use as a context manager to
guarantee server-side cleanup::

    with CamofoxClient() as cb:
        cb.navigate("https://example.com")
        text = cb.snapshot()["snapshot"]

The class is intentionally thin — all higher-level rendering (a11y tree
to markdown, error retry, multi-tab orchestration) belongs upstream in
the skill scripts.
"""

from __future__ import annotations

import logging
import uuid
from types import TracebackType
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://127.0.0.1:9377"
DEFAULT_TIMEOUT_SECONDS = 30.0
NAVIGATE_TIMEOUT_SECONDS = 60.0


class CamofoxError(Exception):
    """Raised on a non-success response from the Camofox server."""


class CamofoxUnavailable(CamofoxError):
    """Raised when the Camofox server is unreachable (down / not installed)."""


class CamofoxClient:
    """Thin HTTP client for Camofox-browser REST API."""

    def __init__(
        self,
        base_url: str = DEFAULT_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        user_id: str | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._http = httpx.Client(timeout=timeout)
        self._user_id = user_id or f"geniriclaw-{uuid.uuid4().hex[:12]}"
        self._tab_id: str | None = None
        self._session_open = False

    # -- Lifecycle ------------------------------------------------------------

    def __enter__(self) -> CamofoxClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Release the server-side session and close the underlying HTTP client.

        Best-effort: errors during cleanup are swallowed because the most
        common cause is that the server is already gone.
        """
        if self._session_open:
            try:
                self._http.delete(
                    f"{self._base}/sessions/{self._user_id}",
                    timeout=5.0,
                )
            except httpx.HTTPError:
                logger.debug("Camofox session cleanup failed", exc_info=True)
            self._session_open = False
            self._tab_id = None
        self._http.close()

    # -- Health ---------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """Return the server's ``/health`` payload, or raise CamofoxUnavailable."""
        try:
            resp = self._http.get(f"{self._base}/health", timeout=5.0)
        except httpx.ConnectError as e:
            msg = f"Camofox server unreachable at {self._base}: {e}"
            raise CamofoxUnavailable(msg) from e
        except httpx.HTTPError as e:
            raise CamofoxError(f"Health check failed: {e}") from e
        if resp.status_code != 200:
            msg = f"Health check returned HTTP {resp.status_code}"
            raise CamofoxError(msg)
        return resp.json()

    # -- Internal HTTP --------------------------------------------------------

    def _post(self, path: str, body: dict[str, Any], *, timeout: float | None = None) -> dict[str, Any]:
        try:
            resp = self._http.post(
                f"{self._base}{path}",
                json=body,
                timeout=timeout or self._timeout,
            )
        except httpx.ConnectError as e:
            raise CamofoxUnavailable(f"Camofox unreachable: {e}") from e
        if resp.status_code >= 400:
            raise CamofoxError(f"POST {path} -> HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            resp = self._http.get(f"{self._base}{path}", params=params, timeout=self._timeout)
        except httpx.ConnectError as e:
            raise CamofoxUnavailable(f"Camofox unreachable: {e}") from e
        if resp.status_code >= 400:
            raise CamofoxError(f"GET {path} -> HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def _get_raw(self, path: str, params: dict[str, Any] | None = None) -> bytes:
        try:
            resp = self._http.get(f"{self._base}{path}", params=params, timeout=self._timeout)
        except httpx.ConnectError as e:
            raise CamofoxUnavailable(f"Camofox unreachable: {e}") from e
        if resp.status_code >= 400:
            raise CamofoxError(f"GET {path} -> HTTP {resp.status_code}")
        return resp.content

    # -- Tab provisioning -----------------------------------------------------

    def _ensure_tab(self, initial_url: str = "about:blank") -> str:
        """Create a tab on first use and return its id (cached afterwards)."""
        if self._tab_id is not None:
            return self._tab_id
        data = self._post(
            "/tabs",
            {
                "userId": self._user_id,
                "sessionKey": self._user_id,
                "url": initial_url,
            },
        )
        tab_id = data.get("tabId") or data.get("id") or data.get("tab_id")
        if not tab_id:
            raise CamofoxError(f"Camofox /tabs response missing tab id: {data!r}")
        self._tab_id = str(tab_id)
        self._session_open = True
        return self._tab_id

    # -- Browser actions ------------------------------------------------------

    def navigate(self, url: str) -> dict[str, Any]:
        """Navigate to *url*. Creates the tab on first call."""
        if self._tab_id is None:
            self._ensure_tab(url)
            return {"ok": True, "url": url}
        return self._post(
            f"/tabs/{self._tab_id}/navigate",
            {"userId": self._user_id, "url": url},
            timeout=NAVIGATE_TIMEOUT_SECONDS,
        )

    def snapshot(self) -> dict[str, Any]:
        """Return the accessibility-tree snapshot of the current tab."""
        tab = self._ensure_tab()
        return self._get(f"/tabs/{tab}/snapshot", params={"userId": self._user_id})

    def click(self, ref: str) -> dict[str, Any]:
        """Click the element with the given a11y *ref*."""
        tab = self._ensure_tab()
        return self._post(
            f"/tabs/{tab}/click",
            {"userId": self._user_id, "ref": ref.lstrip("@")},
        )

    def type_text(self, ref: str, text: str, *, submit: bool = False) -> dict[str, Any]:
        """Type *text* into the element with the given *ref*."""
        tab = self._ensure_tab()
        return self._post(
            f"/tabs/{tab}/type",
            {
                "userId": self._user_id,
                "ref": ref.lstrip("@"),
                "text": text,
                "submit": submit,
            },
        )

    def screenshot(self) -> bytes:
        """Return a PNG screenshot of the current tab."""
        tab = self._ensure_tab()
        return self._get_raw(f"/tabs/{tab}/screenshot", params={"userId": self._user_id})

    def console_logs(self) -> list[dict[str, Any]]:
        """Return recent console logs from the current tab."""
        tab = self._ensure_tab()
        data = self._get(f"/tabs/{tab}/console", params={"userId": self._user_id})
        logs = data.get("logs", data) if isinstance(data, dict) else data
        return list(logs) if isinstance(logs, list) else []
