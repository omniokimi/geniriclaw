"""Shared formatting primitives for command response text."""

from __future__ import annotations

import random

from geniriclaw.i18n import t

SEP = "\u2500\u2500\u2500"

# Custom random startup phrases (Russian) \u2014 picked at random per restart.
# Replaces the static i18n "first_start_body" / "reboot_body" defaults.
_FIRST_START_PHRASES = (
    "\u041f\u0440\u0438\u0432\u0435\u0442! \u041d\u0430 \u0441\u0432\u044f\u0437\u0438. \u0427\u0442\u043e \u043e\u0431\u0441\u0443\u0434\u0438\u043c?",
    "\u042f \u0442\u0443\u0442. \u0421 \u0447\u0435\u0433\u043e \u043d\u0430\u0447\u043d\u0451\u043c?",
    "\u0413\u043e\u0442\u043e\u0432 \u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c. \u041e\u043f\u0438\u0448\u0438 \u0437\u0430\u0434\u0430\u0447\u0443.",
    "\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439. \u0427\u0442\u043e \u043d\u0443\u0436\u043d\u043e \u0441\u0434\u0435\u043b\u0430\u0442\u044c?",
    "\u0411\u043e\u0442 \u043e\u043d\u043b\u0430\u0439\u043d. \u0421\u043f\u0440\u0430\u0448\u0438\u0432\u0430\u0439.",
    "\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u043b\u0441\u044f. \u0416\u0434\u0443 \u0437\u0430\u0434\u0430\u043d\u0438\u0435.",
    "\u042f \u0437\u0434\u0435\u0441\u044c \u0438 \u0441\u043b\u0443\u0448\u0430\u044e.",
    "\u0413\u043e\u0442\u043e\u0432 \u043f\u043e\u043c\u043e\u0447\u044c. \u0421 \u0447\u0435\u0433\u043e \u043d\u0430\u0447\u043d\u0451\u043c?",
    "\u0417\u0430\u043f\u0443\u0449\u0435\u043d. \u041a\u0430\u043a\u0438\u0435 \u043f\u043b\u0430\u043d\u044b?",
    "\u041d\u0430 \u0441\u0432\u044f\u0437\u0438, \u0433\u043e\u0442\u043e\u0432 \u043a \u0440\u0430\u0431\u043e\u0442\u0435.",
)

_REBOOT_PHRASES = (
    "\u041f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u0442\u0438\u043b\u0441\u044f. \u041a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 \u043f\u043e\u0434\u0442\u044f\u043d\u0443\u043b \u2014 \u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0435\u043c.",
    "\u0421\u043d\u043e\u0432\u0430 \u0432 \u044d\u0444\u0438\u0440\u0435. \u0427\u0442\u043e \u043e\u0441\u0442\u0430\u043b\u043e\u0441\u044c?",
    "\u042f \u0432\u0435\u0440\u043d\u0443\u043b\u0441\u044f. \u041a\u0430\u043a\u0438\u0435 \u043f\u043b\u0430\u043d\u044b?",
    "\u0421\u0438\u0441\u0442\u0435\u043c\u044b \u0436\u0438\u0432\u044b. \u041f\u043e\u0435\u0445\u0430\u043b\u0438.",
    "\u041f\u0435\u0440\u0435\u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043f\u0440\u043e\u0448\u043b\u0430, \u043d\u0430 \u0441\u0432\u044f\u0437\u0438.",
    "\u0411\u043e\u0442 \u0441\u043d\u043e\u0432\u0430 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442. \u0427\u0442\u043e \u0434\u0430\u043b\u044c\u0448\u0435?",
    "\u0412\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u043b\u0441\u044f. \u0416\u0434\u0443 \u043a\u043e\u043c\u0430\u043d\u0434.",
    "\u042f \u0442\u0443\u0442. \u041f\u0435\u0440\u0435\u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430.",
    "\u0421\u043d\u043e\u0432\u0430 \u043e\u043d\u043b\u0430\u0439\u043d. \u0427\u0442\u043e \u0443 \u043d\u0430\u0441?",
    "\u0413\u043e\u0442\u043e\u0432 \u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0442\u044c.",
)

_SHELL_TOOLS = frozenset({"bash", "powershell", "cmd", "sh", "zsh", "shell"})

# Map common Claude/Codex/Gemini tool names to Russian action verbs for
# user-facing display. Keys are compared case-insensitively.
_TOOL_LABELS_RU: dict[str, str] = {
    # Shell/bash family
    "bash": "Запрос",
    "powershell": "Запрос",
    "cmd": "Запрос",
    "sh": "Запрос",
    "zsh": "Запрос",
    "shell": "Запрос",
    "bashoutput": "Вывод",
    "killbash": "Останавливаю",
    "killshell": "Останавливаю",
    # File operations
    "read": "Читаю",
    "write": "Пишу",
    "edit": "Редактирую",
    "multiedit": "Правлю",
    "notebookread": "Читаю блокнот",
    "notebookedit": "Правлю блокнот",
    # Search
    "grep": "Ищу",
    "glob": "Нахожу",
    "ls": "Смотрю",
    # Web
    "webfetch": "Открываю страницу",
    "websearch": "Ищу в сети",
    "fetch": "Открываю страницу",
    # Planning / meta
    "todowrite": "Планирую",
    "exitplanmode": "Завершаю план",
    "askuserquestion": "Уточняю",
    # Agent delegation
    "agent": "Делегирую",
    "task": "Делегирую",
    # Long/background tasks
    "schedulewakeup": "Запланировать",
    "monitor": "Наблюдаю",
    # Utility
    "toolsearch": "Ищу инструмент",
    "skill": "Скилл",
}


def normalize_tool_name(name: str) -> str:
    """Map tool name to Russian action verb for Telegram display.

    Unknown tools (including MCP tools with prefixes) are returned unchanged.
    """
    return _TOOL_LABELS_RU.get(name.lower(), name)


def fmt(*blocks: str) -> str:
    """Join non-empty blocks with double newlines."""
    return "\n\n".join(b for b in blocks if b)


# Known CLI error patterns -> user-friendly short explanation.
_AUTH_PATTERNS = (
    "401",
    "unauthorized",
    "authentication",
    "signing in again",
    "sign in again",
    "token has been",
)
_RATE_PATTERNS = ("429", "rate limit", "too many requests", "quota exceeded")
_CONTEXT_PATTERNS = ("context length", "token limit", "maximum context", "too long")


def classify_cli_error(raw: str) -> str | None:
    """Return a user-facing hint for known CLI error patterns, or None."""
    lower = raw.lower()
    if any(p in lower for p in _AUTH_PATTERNS):
        return t("session.error_auth")
    if any(p in lower for p in _RATE_PATTERNS):
        return t("session.error_rate")
    if any(p in lower for p in _CONTEXT_PATTERNS):
        return t("session.error_context")
    return None


def session_error_text(model: str, cli_detail: str = "") -> str:
    """Build the error message shown to the user on CLI failure."""
    base = fmt(t("session.error_header"), SEP, t("session.error_body", model=model))
    hint = classify_cli_error(cli_detail) if cli_detail else None
    if hint:
        return fmt(base, t("session.error_cause", hint=hint))
    if cli_detail:
        # Show first meaningful line, truncated.
        detail = cli_detail.strip().split("\n")[0][:200]
        return fmt(base, t("session.error_detail", detail=detail))
    return base


def timeout_error_text(model: str, timeout_seconds: float) -> str:
    """Build the error message shown when the CLI times out."""
    minutes = int(timeout_seconds / 60)
    return fmt(
        t("timeout.error_header"), SEP, t("timeout.error_body", model=model, minutes=minutes)
    )


def new_session_text(provider: str) -> str:
    """Build /new response for provider-local reset."""
    provider_label = {"claude": "Claude", "codex": "Codex", "gemini": "Gemini"}.get(
        provider.lower(), provider
    )
    return fmt(
        t("session.reset_header"),
        SEP,
        t("session.reset_body", provider=provider_label),
    )


def stop_text(killed: bool, provider: str) -> str:
    """Build the /stop response."""
    body = t("stop.killed", provider=provider) if killed else t("stop.nothing")
    return fmt(t("stop.header"), SEP, body)


# -- Timeout messages --


def timeout_warning_text(remaining: float) -> str:
    """Warning text shown when a timeout is approaching."""
    if remaining >= 60:
        mins = int(remaining // 60)
        return t("timeout.warning_minutes", mins=mins)
    secs = int(remaining)
    return t("timeout.warning_seconds", secs=secs)


def timeout_extended_text(extension: float, remaining_ext: int) -> str:
    """Notification that the timeout was extended due to activity."""
    secs = int(extension)
    return t("timeout.extended", secs=secs, remaining=remaining_ext)


def timeout_result_text(elapsed: float, configured: float) -> str:
    """Error text when a CLI process hit its timeout."""
    return fmt(
        t("timeout.result_header"),
        SEP,
        t("timeout.result_body", elapsed=int(elapsed), configured=int(configured)),
    )


# -- Startup lifecycle messages --


def _try_ai_contextual_greeting() -> str | None:
    """Try to generate a memory-aware greeting via Claude CLI (v2.0 feature).

    Reads ``~/.geniriclaw/workspace/memory_system/MAINMEMORY.md`` and asks
    Claude (via subprocess) to produce a 1–2 sentence Russian greeting that
    references the last conversation context.  Result is cached in
    ``~/.geniriclaw/state/last_greeting.json`` keyed by sha256 of MAINMEMORY,
    so the network call only happens when memory actually changes.

    Returns the greeting text, or ``None`` on any failure (caller falls back
    to the random phrase pool).  Never raises.
    """
    import hashlib
    import json
    import os
    import pathlib
    import shutil
    import subprocess

    try:
        home = pathlib.Path.home()
        memory_path = home / ".geniriclaw" / "workspace" / "memory_system" / "MAINMEMORY.md"
        cache_path = home / ".geniriclaw" / "state" / "last_greeting.json"

        if not memory_path.is_file():
            return None
        memory_text = memory_path.read_text(encoding="utf-8", errors="ignore")
        if len(memory_text.strip()) < 100:
            return None

        memory_hash = hashlib.sha256(memory_text.encode("utf-8")).hexdigest()
        try:
            if cache_path.is_file():
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
                if cache.get("hash") == memory_hash and cache.get("greeting"):
                    return str(cache["greeting"])
        except Exception:
            pass

        claude_bin = shutil.which("claude") or "/usr/local/bin/claude"
        if not pathlib.Path(claude_bin).exists():
            return None

        truncated = memory_text[:4000]
        prompt = (
            "Ты — личный ассистент пользователя. Сгенерируй ОДНО короткое "
            "(1–2 предложения) тёплое приветствие на русском, в котором ты "
            "ссылаешься на последний контекст разговора из памяти ниже. "
            "Стиль — живой, личный, как у близкого помощника. ЗАПРЕЩЕНО "
            "использовать слова: «снова», «в строю», «на связи», «вернулся», "
            "«перезагрузка», «перезапуск», «восстановлен» (звучат как "
            "поломка и починка). Не используй кавычки, эмодзи, markdown — "
            "только текст приветствия.\n\nКонтекст памяти:\n" + truncated
        )

        env = os.environ.copy()
        result = subprocess.run(
            [claude_bin, "-p", prompt, "--model", "haiku"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=20,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            return None
        greeting = (result.stdout or "").strip().strip('"').strip("'")
        if not greeting or len(greeting) > 400 or "\n\n" in greeting:
            return None
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(
                    {"hash": memory_hash, "greeting": greeting},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass
        return greeting
    except Exception:
        return None


def startup_notification_text(kind: str) -> str:
    """Notification text for startup events (v2.0).

    - ``first_start``: tries to generate an AI greeting from MAINMEMORY,
      falls back to a random phrase from ``_FIRST_START_PHRASES``.
    - ``system_reboot`` / ``service_restart``: silent (empty string) —
      avoids interrupting an ongoing conversation with a contextless
      "I'm back" message. v1.0-light sent a reboot phrase; v2.0 keeps
      reboots silent (use ``v1.0-light`` tag if you prefer the old behavior).
    """
    if kind != "first_start":
        return ""
    contextual = _try_ai_contextual_greeting()
    if contextual:
        return contextual
    return random.choice(_FIRST_START_PHRASES)


# -- Auto-recovery messages --


def format_technical_footer(
    model_name: str,
    total_tokens: int,
    input_tokens: int,
    cost_usd: float,
    duration_ms: float | None,
) -> str:
    """Format technical metadata as a footer line."""
    output_tokens = total_tokens - input_tokens
    parts = [t("footer.model", name=model_name)]
    parts.append(t("footer.tokens", total=total_tokens, input=input_tokens, output=output_tokens))
    if cost_usd > 0:
        parts.append(t("footer.cost", cost=f"{cost_usd:.4f}"))
    if duration_ms is not None:
        secs = duration_ms / 1000
        parts.append(t("footer.time", secs=f"{secs:.1f}"))
    return "\n---\n" + " | ".join(parts)


def recovery_notification_text(
    kind: str,
    prompt_preview: str,
    session_name: str = "",
) -> str:
    """Notification that interrupted work is being recovered."""
    preview = prompt_preview[:80] + ("…" if len(prompt_preview) > 80 else "")
    if kind == "named_session":
        return fmt(
            t("recovery.named_header"),
            SEP,
            t("recovery.named_body", session=session_name, preview=preview),
        )
    return fmt(
        t("recovery.interrupted_header"),
        SEP,
        t("recovery.interrupted_body", preview=preview),
    )
