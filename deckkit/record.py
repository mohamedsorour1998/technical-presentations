#!/usr/bin/env python3
"""recordkit — run a demonstration's real commands and render them as video.

    from recordkit import Session, run, encode, cli

    def demo_thing(session):
        session.type_command("some --command")
        out, elapsed = run(["some", "--command"])
        session.wait(elapsed, "working")
        session.output(out, kind="ok")
        session.hold()

    cli({"thing": demo_thing})

WHAT LIVES HERE AND WHAT DOES NOT
=================================
This module knows how to execute a command, remember its real output and timing, and
draw a terminal session as frames. It knows nothing about any particular demonstration.
The demos themselves belong in a script beside it.

WHY RENDER RATHER THAN SCREEN-CAPTURE
=====================================
The commands below are executed for real and their actual stdout is what appears in the
frames -- nothing is typed by hand into a script. Rendering that captured output, instead
of filming the screen, buys four things that matter for a projected talk:

  * TYPE SIZE IS CHOSEN, not inherited from whatever the terminal happened to be set to.
  * NOTHING ELSE IS IN SHOT. No notification, no menu bar, no other window, no cursor
    wandering across the frame.
  * THE PALETTE IS THE DECK'S. The video sits inside the slide instead of on top of it.
  * IT REGENERATES. If a measurement moves, re-run this and the video agrees with the
    slide again; a screen capture would quietly drift out of date.

WAITS ARE COMPRESSED, AND SAID SO ON SCREEN
===========================================
A training run takes about ninety seconds and a transcription thirteen. Played back at
life size, the video would be exactly the dead air that made these demonstrations
unsuitable for the stage. So a long wait is shown as a brief animated ellipsis with the
REAL elapsed time printed beside it, e.g. "... 1m 29s". The time is measured, the waiting
is not re-enacted. Anything under `LIVE_SECONDS` plays at its true length.

The honest framing for the audience is on the slide: these are recordings of real runs on
the presenting laptop, with the pauses shortened.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = pathlib.Path("video")   # a talk sets this: record.OUT_DIR = ...
FFMPEG = "/opt/homebrew/bin/ffmpeg"
MENLO = "/System/Library/Fonts/Menlo.ttc"

# 16:9 at a size that stays crisp on a projector without inflating the .pptx.
W, H = 1600, 900
FPS = 24
PAD_X, PAD_Y = 56, 48
SIZE = 30
LINE_H = 42

# The deck palette. These are the same values as scripts/build_deck.py; the video has to
# look like part of the slide rather than a window resting on it.
BG = (0x07, 0x09, 0x0C)
INK = (0xE8, 0xED, 0xF4)
DIM = (0x8A, 0x94, 0xA6)
CYAN = (0x4F, 0xD1, 0xC5)
ROSE = (0xFF, 0x6B, 0x6B)
MINT = (0x4A, 0xDE, 0x80)

TYPE_CPS = 45          # characters per second while a command "types"
LIVE_SECONDS = 6.0     # waits at or under this play at their real length
WAIT_SHOWN = 1.6       # a compressed wait occupies this many seconds of video
HOLD_END = 2.5         # freeze on the final frame, so the last line can be read


def _font(bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(MENLO, SIZE, index=1 if bold else 0)


def _chars_per_line() -> int:
    """How many monospace characters fit between the margins, with one to spare."""
    advance = _font().getlength("M" * 100) / 100
    return int((W - 2 * PAD_X) // advance) - 1


def _colour(kind: str) -> tuple[int, int, int]:
    return {"cmd": INK, "out": DIM, "note": DIM, "ok": MINT, "bad": ROSE,
            "prompt": CYAN}[kind]


def _draw(lines: list[tuple[str, str]], caption: str | None,
          height: int = H) -> Image.Image:
    """One frame. `lines` is [(kind, text), ...] already trimmed to what fits."""
    image = Image.new("RGB", (W, height), BG)
    pen = ImageDraw.Draw(image)

    y = PAD_Y
    for kind, text in lines:
        bold = kind in ("ok", "bad")
        pen.text((PAD_X, y), text, font=_font(bold), fill=_colour(kind))
        y += LINE_H

    if caption:
        # Bottom-right, dim: the elapsed time of a wait that was shortened. It is the one
        # piece of text on screen that did not come from the terminal, so it is set apart.
        font = _font()
        width = pen.textlength(caption, font=font)
        pen.text((W - PAD_X - width, height - PAD_Y // 2 - SIZE), caption,
                 font=font, fill=CYAN)
    return image


def _wrap(text: str, limit: int) -> list[str]:
    """Hard-wrap on width, the way a terminal does -- no word breaking cleverness."""
    if not text:
        return [""]
    return [text[i:i + limit] for i in range(0, len(text), limit)] or [""]


class Session:
    """Records a session as a script of frames, then draws them.

    TWO PASSES, because the frame height depends on the tallest moment of the session and
    that is not known until the session has finished running. Drawing immediately meant
    every video was a fixed 16:9 with the content stranded in the top third and a large
    empty area beneath it. Collecting the frames first lets the image be sized to the
    content, so the video fills whatever box it is given on the slide.
    """

    def __init__(self, work: pathlib.Path):
        self.work = work
        self.script: list[tuple[list[tuple[str, str]], str | None, int]] = []
        self.lines: list[tuple[str, str]] = []
        # MEASURED FROM THE FONT, not assumed. A hardcoded 17px advance was five pixels
        # per character too narrow at this size, so every long line wrapped about five
        # characters late and those characters were drawn past the right edge -- losing a
        # letter mid-word, invisibly, in a video nobody can pause to query.
        self.limit = _chars_per_line()

    @property
    def frames(self) -> int:
        return sum(count for _, _, count in self.script)

    def _emit(self, count: int = 1, caption: str | None = None) -> None:
        self.script.append((list(self.lines), caption, max(1, count)))

    def render(self) -> int:
        """Draw every scripted frame at a height that fits the whole session."""
        rows = max((len(lines) for lines, _, _ in self.script), default=1)
        height = PAD_Y * 2 + rows * LINE_H
        height += height % 2                     # H.264 needs even dimensions
        index = 0
        for lines, caption, count in self.script:
            image = _draw(lines, caption, height)
            for _ in range(count):
                index += 1
                image.save(self.work / f"{index:05d}.png")
        return index

    def type_command(self, *lines: str) -> None:
        """Show a command appearing at a readable typing speed.

        ONLY THE FIRST LINE CARRIES THE PROMPT. An earlier version wrapped a long command
        and prefixed every wrapped segment with "$ ", so one command read on screen as
        three separate commands -- the exact misreading a recorded demo cannot afford,
        because nobody can ask about it afterwards. Continuations are indented instead,
        which is what a shell shows.

        Callers pass the line breaks they want, so a long command breaks at a readable
        place rather than wherever the frame width happens to fall.
        """
        for position, line in enumerate(lines):
            prefix = "$ " if position == 0 else "  "
            self.lines.append(("prompt", prefix))
            index = len(self.lines) - 1
            for step in range(1, len(line) + 1):
                self.lines[index] = ("prompt", prefix + line[:step])
                if step % 3 == 0 or step == len(line):
                    self._emit(max(1, int(FPS / TYPE_CPS * 3)))
        self._emit(int(FPS * 0.35))

    def output(self, text: str, kind: str = "out", pace: float = 0.5) -> None:
        """Print captured output, a few lines at a time."""
        for raw in text.rstrip("\n").split("\n"):
            for line in _wrap(raw.rstrip(), self.limit):
                self.lines.append((kind, line))
            self._emit(max(1, int(FPS * pace / 8)))
        self._emit(int(FPS * 0.3))

    def wait(self, seconds: float, label: str) -> None:
        """Represent a real wait. Short ones play out; long ones are compressed."""
        shown = seconds if seconds <= LIVE_SECONDS else WAIT_SHOWN
        caption = None if seconds <= LIVE_SECONDS else f"actual: {_human(seconds)}"
        self.lines.append(("note", ""))
        index = len(self.lines) - 1
        ticks = max(1, int(shown * 4))
        for tick in range(ticks):
            self.lines[index] = ("note", "." * (tick % 4))
            self._emit(max(1, int(FPS * shown / ticks)), caption=caption)
        self.lines.pop(index)

    def hold(self) -> None:
        self._emit(int(FPS * HOLD_END))


def _human(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    return f"{int(seconds // 60)}m {int(seconds % 60):02d}s"


CACHE = pathlib.Path("bench/recorded-output.json")  # a talk may reset this
REUSE = False   # set by --reuse; read inside run()


def _cache() -> dict:
    import json
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def run(command: list[str], cwd: pathlib.Path | None = None,
        env: dict | None = None, *, reuse: bool | None = None) -> tuple[str, float]:
    """Execute for real, or replay the last real run.

    CACHED, because rendering and running are different problems. Every adjustment to how
    a frame looks used to re-execute the commands behind it -- and one of those is an
    agent call that took sixty-five seconds on a good day and thirteen minutes on the day
    the model server died mid-request. The output and its true elapsed time are stored
    after each real run, so `--reuse` re-renders from them instantly.

    The cache holds real measurements from a real run; it is not a substitute for one.
    Recording without `--reuse` always re-executes.
    """
    import json
    import os

    # THE DEFAULT COMES FROM THE MODULE FLAG, not from each call site. Threading an
    # argument through every call meant five of them silently kept re-executing, which is
    # the opposite of what --reuse is for and cost three ten-minute hangs to notice.
    if reuse is None:
        reuse = REUSE

    key = " ".join(command)
    store = _cache()
    if reuse and key in store:
        entry = store[key]
        return entry["output"], entry["elapsed"]

    merged = {**os.environ, "HF_HUB_OFFLINE": "1", **(env or {})}
    start = time.perf_counter()
    done = subprocess.run(command, cwd=str(cwd or ROOT), env=merged,
                          capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - start
    output = done.stdout + done.stderr

    store[key] = {"output": output, "elapsed": elapsed,
                  "recorded": time.strftime("%Y-%m-%d %H:%M:%S")}
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(store, indent=2) + "\n")
    return output, elapsed


def encode(work: pathlib.Path, name: str) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.mp4"
    subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
         "-framerate", str(FPS), "-i", str(work / "%05d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "30",
         "-movflags", "+faststart", str(out)],
        check=True)
    # The poster frame is the LAST frame, not the first: a slide showing a finished
    # session reads as a result, while one showing an empty prompt reads as broken.
    subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
         "-sseof", "-0.1", "-i", str(out), "-frames:v", "1",
         str(OUT_DIR / f"{name}.png")], check=True)
    return out



def _strip_ansi(text: str) -> str:
    """Remove colour codes and carriage returns an interactive tool leaves behind."""
    import re
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text).replace("\r", "")



def cli(demos: dict, *, out_dir: pathlib.Path | None = None) -> int:
    """Command-line entry point for a set of demos. See the module docstring."""
    global REUSE, OUT_DIR
    parser = argparse.ArgumentParser(description="record a demonstration as video")
    parser.add_argument("demo", nargs="?", choices=sorted(demos))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--reuse", action="store_true",
                        help="re-render from the last real run instead of re-executing")
    args = parser.parse_args()

    if out_dir is not None:
        OUT_DIR = out_dir
    if args.list or not args.demo:
        print("  demos:", ", ".join(sorted(demos)))
        return 0

    REUSE = args.reuse
    work = pathlib.Path("/tmp") / f"record-{args.demo}"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    session = Session(work)
    print(f"  {'re-rendering' if REUSE else 'running'} {args.demo} ...")
    demos[args.demo](session)
    print(f"  {session.frames} frames -> drawing")
    session.render()
    print("  encoding")
    out = encode(work, args.demo)
    shutil.rmtree(work, ignore_errors=True)
    print(f"  wrote {out}  ({out.stat().st_size // 1024} KB, "
          f"{session.frames / FPS:.1f}s)")
    return 0
