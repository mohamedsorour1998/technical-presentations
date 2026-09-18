#!/usr/bin/env python3
"""Measure the local language model on this machine, for the talk's numbers.

    # needs the server running:
    mlx_lm.server --model mlx-community/Qwen3.5-4B-MLX-4bit --port 8080
    python3 talks/bringing-the-model-home/bench_lm.py

Writes bench/lm.json. Every figure quoted on a slide has to come from a command someone
can re-run, and it has to be measured on the machine doing the presenting -- a Studio
number would be a different talk.

WHAT IS WORTH MEASURING, AND WHY
  prompt tokens/sec      how fast it reads. In an agentic loop this dominates: tool
                         output gets re-read on every turn, so hundreds of thousands of
                         tokens are processed and only a few thousand generated.
  generation tokens/sec  how fast it writes. The number everyone quotes, and the less
                         important of the two for agent work.
  peak memory            the figure that decides whether a model runs on 16 GB at all.
  wall clock per turn    what the room actually experiences while standing there.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:8080/v1"
MODEL = "mlx-community/Qwen3.5-4B-MLX-4bit"

# Short, medium and long prompts: the point is to show that a LONG prompt is the
# expensive part, which is what makes the agentic loop slow.
PROMPTS = [
    ("short", "Answer in one sentence: what is unified memory?"),
    ("medium", "In three sentences, explain why memory bandwidth limits how fast a "
               "language model generates text on a laptop."),
]


def post(messages: list[dict], *, base_url: str, model: str, max_tokens: int) -> tuple[dict, float]:
    """One completion. Returns the parsed body and the wall-clock seconds it took."""
    body = json.dumps({
        "model": model, "messages": messages, "max_tokens": max_tokens,
        "temperature": 0.0, "chat_template_config": {"enable_thinking": False},
    }).encode()
    request = urllib.request.Request(
        f"{base_url}/chat/completions", data=body,
        headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = json.load(response)
    except urllib.error.URLError as error:
        sys.exit(f"cannot reach {base_url} — is mlx_lm.server running?\n  {error}")
    return payload, time.perf_counter() - start


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--max-tokens", type=int, default=120)
    args = parser.parse_args()

    # A long prompt built from the repo's own transcripts, so the "reads fast" number is
    # measured on realistic context rather than on a synthetic wall of tokens.
    corpus = (ROOT / "wwdc2026-232.txt").read_text()[:12000]
    prompts = [*PROMPTS, ("long-context",
                          f"Here is a transcript:\n\n{corpus}\n\n"
                          "In one sentence, what is the main claim?")]

    rows = []
    for label, prompt in prompts:
        payload, elapsed = post([{"role": "user", "content": prompt}],
                                base_url=args.base_url, model=args.model,
                                max_tokens=args.max_tokens)
        usage = payload.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        rows.append({
            "prompt": label,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "wall_seconds": round(elapsed, 2),
            "tokens_per_second_overall": round(
                (prompt_tokens + completion_tokens) / elapsed, 1),
        })
        print(f"{label:<14}{prompt_tokens:>7} in {completion_tokens:>5} out "
              f"{elapsed:>7.2f}s")

    machine = {
        "chip": subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                               capture_output=True, text=True, check=False).stdout.strip(),
        "memory_gib": round(int(subprocess.run(["sysctl", "-n", "hw.memsize"],
                            capture_output=True, text=True, check=False).stdout) / 2**30),
        "macos": platform.mac_ver()[0],
        "model": args.model,
    }
    out = ROOT / "bench" / "lm.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"machine": machine, "results": rows}, indent=2) + "\n")
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
