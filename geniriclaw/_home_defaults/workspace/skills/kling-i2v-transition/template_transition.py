#!/usr/bin/env python3
"""kling_transition.py — image→video через Kling v2.1 standard.

Usage:
    REPLICATE_API_TOKEN=... python3 kling_transition.py \\
        --start <URL> --end <URL_optional> \\
        --prompt "<motion prompt>" --duration 5 \\
        --output /absolute/path/output.mp4

Requires: Replicate API token, публичные URL для start/end изображений.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

API_BASE = "https://api.replicate.com/v1/models/kwaivgi/kling-v2.1-standard/predictions"
POLL_BASE = "https://api.replicate.com/v1/predictions"
NEGATIVE_DEFAULT = (
    "jump cut, flicker, strobe, double exposure, identity change, "
    "face morph, distorted features, extra limbs, malformed hands, "
    "AI artifacts, sudden lighting change"
)


def post(url: str, token: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "wait=0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="Public URL of start image")
    p.add_argument("--end", default=None, help="Public URL of end image (optional)")
    p.add_argument("--prompt", required=True, help="Motion/camera description")
    p.add_argument("--negative", default=NEGATIVE_DEFAULT, help="Negative prompt")
    p.add_argument("--duration", type=int, choices=[5, 10], default=5)
    p.add_argument("--output", required=True, help="Absolute path for output .mp4")
    p.add_argument("--max-poll-seconds", type=int, default=300)
    args = p.parse_args()

    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        sys.exit("ERROR: REPLICATE_API_TOKEN not set in environment")

    payload: dict = {
        "input": {
            "start_image": args.start,
            "prompt": args.prompt,
            "negative_prompt": args.negative,
            "duration": args.duration,
        }
    }
    if args.end:
        payload["input"]["end_image"] = args.end

    print(f"[create] model=kling-v2.1-standard duration={args.duration}s")
    resp = post(API_BASE, token, payload)
    pred_id = resp.get("id")
    if not pred_id:
        sys.exit(f"ERROR: create failed: {resp}")
    print(f"[poll] prediction id={pred_id}")

    poll_url = f"{POLL_BASE}/{pred_id}"
    started = time.time()
    while True:
        if time.time() - started > args.max_poll_seconds:
            sys.exit("ERROR: poll timeout")
        time.sleep(5)
        status = get(poll_url, token)
        state = status.get("status")
        print(f"  status={state}")
        if state == "succeeded":
            video_url = status.get("output")
            break
        if state in ("failed", "canceled"):
            err = status.get("error") or status
            sys.exit(f"ERROR: generation {state}: {err}")

    if not video_url:
        sys.exit("ERROR: no output URL in succeeded response")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    print(f"[download] {video_url} → {args.output}")
    urllib.request.urlretrieve(video_url, args.output)
    size = os.path.getsize(args.output)
    print(f"[ok] saved {size} bytes")


if __name__ == "__main__":
    main()
