#!/usr/bin/env python3
"""One-shot fetch: open a URL in Camofox and emit its accessibility-tree snapshot.

Usage:
    python3 fetch.py <url>            # default 8s settle wait
    python3 fetch.py <url> --wait 15  # custom settle wait in seconds
    python3 fetch.py <url> --raw      # also include screenshot path

Exit codes:
    0  — success, snapshot on stdout
    1  — usage error or unexpected failure
    2  — Camofox server unreachable (caller should fall back to web_fetch)

Designed to be invoked by the Claude `camofox-browser` skill via Bash.
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    from geniriclaw.infra.camofox import (
        CamofoxClient,
        CamofoxError,
        CamofoxUnavailable,
    )
except ImportError as e:
    sys.stderr.write(
        f"camofox-browser skill: cannot import geniriclaw.infra.camofox ({e}).\n"
        "Make sure you are running with the geniriclaw pipx Python.\n"
    )
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch a URL via Camofox and print its a11y snapshot.")
    parser.add_argument("url", help="URL to navigate to")
    parser.add_argument("--wait", type=float, default=8.0,
                        help="Seconds to wait after navigate for JS to settle (default 8)")
    args = parser.parse_args()

    try:
        with CamofoxClient() as cb:
            try:
                health = cb.health()
            except CamofoxUnavailable as e:
                sys.stderr.write(
                    f"Camofox server is not reachable: {e}\n"
                    "Run `geniriclaw camofox start` and retry.\n"
                )
                return 2
            if not health.get("ok"):
                sys.stderr.write(f"Camofox health check failed: {health!r}\n")
                return 2

            cb.navigate(args.url)
            time.sleep(max(0.0, args.wait))
            snap = cb.snapshot()
    except CamofoxUnavailable as e:
        sys.stderr.write(f"Camofox unreachable: {e}\n")
        return 2
    except CamofoxError as e:
        sys.stderr.write(f"Camofox request failed: {e}\n")
        return 1

    text = snap.get("snapshot", "") if isinstance(snap, dict) else ""
    if not text:
        sys.stderr.write(f"Camofox returned empty snapshot for {args.url}\n")
        return 1

    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
