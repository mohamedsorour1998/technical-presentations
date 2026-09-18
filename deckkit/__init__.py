"""deckkit — build technical conference decks as .pptx, and record their demos as video.

    from deckkit.deck import *            # palette, primitives, charts, build, verify
    from deckkit.record import Session, run, cli

`deck` draws slides and verifies the saved file. `record` runs a demonstration's real
commands and renders them as video. Neither knows anything about a particular talk;
content lives under talks/.
"""
