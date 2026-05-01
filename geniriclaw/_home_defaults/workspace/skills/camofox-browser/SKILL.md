---
name: camofox-browser
description: Use this skill ONLY after a normal web_fetch fails with HTTP 999/403/empty JS shell, OR when the user explicitly asks the agent to browse, click, fill a form, or take a screenshot. It runs a real Firefox-based browser (Camoufox) with C++ anti-fingerprinting, available locally at http://127.0.0.1:9377 inside geniriclaw. NOT for static HTML pages — those should keep using web_fetch (cheaper, faster, no subprocess).
---

# Camofox Browser

A real, anti-detection browser for tasks that fail or are impossible with `web_fetch`.

## When to use this skill

Use **only** when at least one of these is true:

- `web_fetch` returned **HTTP 999** (LinkedIn), **HTTP 403**, or other bot-detection.
- The page is a JS-rendered shell (`web_fetch` returned a near-empty `<div id="root">`).
- The user explicitly asked to browse, click, type, screenshot, or "see the page like a human".
- A multi-step flow is needed (form → submit → next page).

Do **not** use for plain HTML pages, RSS feeds, or simple JSON APIs — `web_fetch` is faster, cheaper, and does not spawn a subprocess.

## Quick fetch (most common case)

For a one-shot "give me the readable content of this URL", run:

```bash
python3 ~/.geniriclaw/workspace/skills/camofox-browser/fetch.py "<url>"
```

The script:
1. Opens the URL in Camofox.
2. Waits for the page to settle.
3. Returns the accessibility-tree snapshot (≈ rendered text + clickable refs).
4. Closes the session cleanly.

stdout = the readable content, ready to summarise to the user.
exit code 0 = success; 2 = server unavailable (then fall back to `web_fetch` and explain to the user).

## Multi-step browsing (advanced)

When the user needs interaction, use the Python client directly:

```python
from geniriclaw.infra.camofox import CamofoxClient

with CamofoxClient() as cb:
    cb.navigate("https://example.com/login")
    snap = cb.snapshot()
    # snap["snapshot"] contains a11y tree with element refs like [e1], [e2]
    cb.type_text("e3", "user@example.com")
    cb.type_text("e4", "secret")
    cb.click("e5")  # submit button
    final = cb.snapshot()
```

Each element in the snapshot has a `[eN]` ref — pass that ref to `click()` / `type_text()`.

## Server lifecycle

The Camofox server is managed by geniriclaw as a LaunchAgent (`dev.geniri.camofox`).
- Status: `geniriclaw camofox status`
- Restart: `geniriclaw camofox restart`
- Logs: `~/.geniriclaw/camofox/logs/{stdout,stderr}.log`

If `fetch.py` exits with code 2, run `geniriclaw camofox status` to diagnose, then `geniriclaw camofox start`. After start, retry the fetch.

## Known site notes

- **LinkedIn**: profile pages load fully but show a Sign-in modal. To read public-only content, click the `Dismiss` button in the snapshot first.
- **Sites with hard CAPTCHA**: Camofox does not solve CAPTCHA; if you hit one, tell the user.
- **Sites that detect Camofox specifically**: rare; report to the user if all attempts fail with the same wall.

## What NOT to do

- Don't loop `fetch.py` against many URLs at once (each call opens a fresh session — slow). For ≥3 URLs use a single Python script with one `CamofoxClient`.
- Don't try to bypass paid content / login walls — the user must provide credentials.
- Don't keep `CamofoxClient` open across tool calls — close it (or use `with`).
