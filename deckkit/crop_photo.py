#!/usr/bin/env python3
"""Crop a portrait to the square the deck needs.

    .venv-deck/bin/python scripts/crop_photo.py <source image> [--name sorour]

Writes pitch/photos/square/<name>.jpg at 640x640.

WHY THE CROP HAPPENS ON DISK AND NOT IN THE DECK. CSS can crop on the fly with
`object-fit: cover`; PowerPoint has no equivalent. A non-square image placed in a square
or oval frame is STRETCHED, and a stretched face is the one defect an audience notices
immediately. So the crop is done once, here, and both the generated deck and the browser
preview show the same already-square file.

WHY THE CROP IS BIASED UPWARD. A centre crop on a tall portrait takes equal amounts off
the top and the bottom, which cuts the top of the head off. Taking 12% of the surplus from
the top and the rest from the bottom keeps the head intact and the eyes near the upper
third, which is where a portrait wants them.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "pitch" / "photos" / "square"
SIDE = 640


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("--name", default="sorour", help="output stem")
    args = parser.parse_args()

    if not args.source.exists():
        sys.exit(f"no such file: {args.source}")

    image = Image.open(args.source)
    if image.mode != "RGB":
        image = image.convert("RGB")
    width, height = image.size
    side = min(width, height)

    if height > width:
        top = int((height - side) * 0.12)      # keep the head, not the chin
        left = (width - side) // 2
    else:
        left = (width - side) // 2
        top = (height - side) // 2

    square = image.crop((left, top, left + side, top + side))
    square = square.resize((SIDE, SIDE), Image.LANCZOS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.name}.jpg"
    square.save(out, "JPEG", quality=92, optimize=True)

    print(f"  {args.source.name}: {width}x{height} -> {SIDE}x{SIDE}")
    print(f"  crop box ({left}, {top}) size {side}, biased "
          f"{'up' if height > width else 'centre'}")
    print(f"  wrote {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
