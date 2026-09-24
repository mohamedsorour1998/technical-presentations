#!/usr/bin/env python3
"""Build a talk to a TEMPORARY path, leaving its committed deck untouched.

    .venv-deck/bin/python -m deckkit.build_to talks/<name>/build_deck.py /tmp/check.pptx

For the two situations where writing the real `.pptx` is wrong:

- the deck is OPEN in PowerPoint (a `~$<Name>.pptx` lock file sits beside it), and a
  rebuild would race whatever the person saves;
- you are checking that an ENGINE change leaves another talk building, and its
  committed deck should not be rewritten as a side effect.

The talk's own `main()` runs -- every check, the same exit code -- with its `build`
replaced by one that writes to the path given.

BYTECODE IS NOT WRITTEN, and that is load-bearing. The talk is imported as a module, so
Python would cache it in `__pycache__`, and a cache entry is invalidated only by a
change of mtime or size. A RED-step mutation that keeps the file's size (5 -> 8),
reverted within the same second, leaves a cache entry that still validates -- and the
next build runs the MUTATED code while the source on disk is correct. Measured once:
a FAIL reappeared after a verified restore, and cleared when __pycache__ was deleted.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    talk, out = pathlib.Path(argv[0]).resolve(), pathlib.Path(argv[1]).resolve()
    spec = importlib.util.spec_from_file_location(f"talk_{talk.parent.name}", talk)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    real_build = module.build
    module.build = lambda slides, _committed: real_build(slides, out)
    return module.main()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
