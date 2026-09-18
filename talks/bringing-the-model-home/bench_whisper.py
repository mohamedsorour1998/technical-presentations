#!/usr/bin/env python3
"""Measure mlx_whisper throughput on this machine, for the talk's numbers.

    python3 talks/bringing-the-model-home/bench_whisper.py

Every figure quoted on a slide has to come from a command someone can re-run, so this
writes bench/whisper.json alongside the human-readable table. Run it on the presenting
machine -- the whole point of the number is that it is THIS Mac, not a Studio.

The model is loaded from the Hugging Face cache on every invocation, so the first run of
a session pays a cold-start penalty. That penalty is itself worth measuring: it is what
the audience will experience, and `--repeat` separates it from steady-state throughput.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import platform
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
MODEL = "mlx-community/whisper-large-v3-mlx"
WHISPER = pathlib.Path.home() / ".local/bin/mlx_whisper"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def duration(path: pathlib.Path) -> float:
    """Audio length in seconds, from ffprobe rather than from the file size."""
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def transcribe(path: pathlib.Path, outdir: pathlib.Path) -> float:
    """Run mlx_whisper once and return elapsed wall-clock seconds.

    Wall clock, deliberately: it is what the room sees. CPU time would flatter the
    result by hiding the GPU wait.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    result = subprocess.run(
        [str(WHISPER), str(path),
         "--model", MODEL,
         "--language", "en",
         "--condition-on-previous-text", "False",
         "--output-dir", str(outdir),
         "--output-name", path.stem,
         "--output-format", "txt",
         "--verbose", "False"],
        capture_output=True, text=True, check=False,
    )
    elapsed = time.perf_counter() - start
    if result.returncode != 0:
        sys.exit(f"mlx_whisper failed on {path.name}:\n{result.stderr[-2000:]}")
    return elapsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("clips", nargs="*", help="audio files; defaults to clips/*.wav")
    parser.add_argument("--repeat", type=int, default=2,
                        help="runs per clip; run 1 is cold, later runs are warm")
    args = parser.parse_args()

    clips = ([pathlib.Path(c) for c in args.clips]
             or sorted((ROOT / "clips").glob("*.wav")))
    if not clips:
        sys.exit("no clips found; cut some into clips/ first")

    rows = []
    for clip in clips:
        secs = duration(clip)
        runs = [transcribe(clip, ROOT / "bench") for _ in range(args.repeat)]
        rows.append({"clip": clip.name, "audio_seconds": round(secs, 1),
                     "runs_seconds": [round(r, 2) for r in runs],
                     "cold_seconds": round(runs[0], 2),
                     "warm_seconds": round(min(runs[1:]) if len(runs) > 1 else runs[0], 2),
                     "warm_realtime_factor": round(
                         secs / (min(runs[1:]) if len(runs) > 1 else runs[0]), 2)})

    machine = {
        "chip": subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                               capture_output=True, text=True, check=False).stdout.strip(),
        "memory_gib": round(int(subprocess.run(["sysctl", "-n", "hw.memsize"],
                            capture_output=True, text=True, check=False).stdout) / 2**30),
        "macos": platform.mac_ver()[0],
        "model": MODEL,
    }

    print(f"{machine['chip']}, {machine['memory_gib']} GiB, macOS {machine['macos']}")
    print(f"model: {MODEL}\n")
    print(f"{'clip':<18}{'audio':>8}{'cold':>9}{'warm':>9}{'warm x RT':>11}")
    for row in rows:
        print(f"{row['clip']:<18}{row['audio_seconds']:>7.1f}s"
              f"{row['cold_seconds']:>8.2f}s{row['warm_seconds']:>8.2f}s"
              f"{row['warm_realtime_factor']:>10.2f}x")

    out = ROOT / "bench" / "whisper.json"
    out.write_text(json.dumps({"machine": machine, "results": rows}, indent=2) + "\n")
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
