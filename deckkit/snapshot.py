#!/usr/bin/env python3
"""Render a deck the way PowerPoint draws it: one PNG per slide, plus the PDF.

    .venv-deck/bin/python -m deckkit.snapshot talks/<name>/pitch/<Name>.pptx /tmp/shots

WHY. verify() ESTIMATES layout from text metrics; it cannot see a rule through a line,
a colour that reads as noise, or a name that wrapped onto a title. Those were found by
a person clicking through the deck -- after the checks passed. This makes that look
repeatable: render, then open the PNGs.

HOW. PowerPoint's AppleScript `save ... as save as PNG` exits 0 and writes nothing
(measured, two forms); `save as PDF` works. So: copy the deck into PowerPoint's sandbox
container (it cannot write elsewhere), open it, export PDF, close without saving, and
split the PDF with PDFKit (deckkit/pdf2png.swift). Needs macOS, PowerPoint and Swift
(Xcode command-line tools). The first run may ask to let the terminal control
PowerPoint; allow it.

It REFUSES a deck that is open in PowerPoint (a ~$<Name>.pptx lock file beside it), and
quits PowerPoint afterwards only if it was not already running.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
SANDBOX = pathlib.Path.home() / "Library/Containers/com.microsoft.Powerpoint/Data/deckkit-snapshot"


def _running() -> bool:
    return subprocess.run(["pgrep", "-f", "Microsoft PowerPoint.app"],
                          capture_output=True).returncode == 0


def _osascript(script: str) -> None:
    run = subprocess.run(["osascript", "-e", script], capture_output=True, text=True,
                         timeout=300, check=False)
    if run.returncode:
        raise RuntimeError(f"PowerPoint scripting failed (exit {run.returncode}): "
                           f"{run.stderr.strip()}")


def _cleanup(name: str, was_running: bool) -> None:
    """Close OUR copy; quit PowerPoint only if this run started it.

    A deck with embedded video can make PowerPoint raise a MODAL prompt during PDF
    export. Scripting then answers "User canceled (-128)" to everything, quit included,
    and the app sits there holding no presentation. Only in that case -- we started it
    and it holds nothing -- is it ended by force. An instance the person was already
    running is never killed.
    """
    try:
        _osascript(f'tell application "Microsoft PowerPoint" to close '
                   f'(every presentation whose name is "{name}") saving no')
    except (RuntimeError, subprocess.TimeoutExpired):
        pass
    if was_running:
        return
    try:
        _osascript('tell application "Microsoft PowerPoint" to quit')
    except (RuntimeError, subprocess.TimeoutExpired):
        pass
    time.sleep(3)
    if _running():
        held = subprocess.run(["osascript", "-e", 'tell application "Microsoft PowerPoint" '
                               'to count presentations'], capture_output=True, text=True,
                              timeout=30, check=False).stdout.strip()
        if held in ("0", ""):
            subprocess.run(["killall", "Microsoft PowerPoint"], check=False)


def snapshot(deck: pathlib.Path, out: pathlib.Path, *, width: int = 1600) -> list[pathlib.Path]:
    deck, out = deck.resolve(), out.resolve()
    if (deck.parent / f"~${deck.name}").exists():
        raise RuntimeError(f"{deck.name} is open in PowerPoint (lock file beside it); "
                           "close it first -- rendering it would race the person's edits")
    was_running = _running()
    SANDBOX.mkdir(parents=True, exist_ok=True)
    copy, pdf = SANDBOX / deck.name, SANDBOX / f"{deck.stem}.pdf"
    shutil.copy2(deck, copy)
    pdf.unlink(missing_ok=True)
    # TWO CALLS, AND A WAIT BETWEEN THEM. `save ... as save as PDF` returns before the
    # file is written; closing straight after it CANCELS the export -- measured as
    # "User canceled (-128)" and no PDF. So export, poll until the PDF exists and its
    # size stops changing, and only then close -- OUR copy, by name, never "every
    # presentation", which would close whatever the person had open.
    try:
        _osascript(f'''tell application "Microsoft PowerPoint"
            open POSIX file "{copy}"
            delay 2
            save active presentation in (POSIX file "{pdf}") as save as PDF
        end tell''')
        last = -1
        for _ in range(180):
            size = pdf.stat().st_size if pdf.exists() else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(1)
    finally:
        _cleanup(copy.name, was_running)
    if not pdf.exists() or pdf.stat().st_size == 0:
        raise RuntimeError(f"PowerPoint wrote no PDF for {deck.name}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy2(pdf, out / pdf.name)
    split = subprocess.run(["swift", str(HERE / "pdf2png.swift"), str(pdf), str(out), str(width)],
                           capture_output=True, text=True, timeout=300, check=False)
    if split.returncode:
        raise RuntimeError(f"pdf2png failed:\n{split.stderr.strip()}")
    copy.unlink(missing_ok=True)
    pngs = sorted(out.glob("slide-*.png"))
    print(f"{deck.name}: {len(pngs)} slides rendered by PowerPoint -> {out}  (+ {pdf.name})")
    return pngs


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        sys.exit(2)
    snapshot(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]),
             width=int(sys.argv[3]) if len(sys.argv) == 4 else 1600)
