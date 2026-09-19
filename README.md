# Technical presentations

Conference talks built the way software is built: the slides are generated from a
committed script, the demonstrations are recorded from real command runs, and every
figure on a slide traces back to the command that produced it.

The build fails if a number contradicts the recording beside it, if text collides, if a
shape leaves the slide, if the XML is out of schema order, or if the prose slips into
shouting capitals.

## Layout

```
CLAUDE.md                     the method — read this first
deckkit/deck.py               the slide engine: palette, primitives, charts, motion, verification
deckkit/record.py             runs a demo's real commands and renders them as video
deckkit/crop_photo.py         square-crops a portrait for the speaker slide
talks/<name>/                 one talk: its constants, slides, demos and deliverables
```

`deckkit` knows nothing about any particular talk. Content lives under `talks/`.

## Getting started

```zsh
uv venv .venv-deck --python 3.13
uv pip install --python .venv-deck/bin/python "python-pptx>=1.0,<2" Pillow

.venv-deck/bin/python talks/bringing-the-model-home/build_deck.py
```

To start a new talk, copy a talk directory, replace the constants and the slide
functions, and leave `deckkit` alone.

## What the toolkit does

**Slides** — 16:9, dark, built from a blank layout with every box positioned by hand.
Bar, line and positioning charts drawn as vector shapes so a projector cannot soften
them. Transitions and click-advanced fade animations written as raw XML, because
`python-pptx` models shapes and text but not the timing tree.

**Recorded demonstrations** — `deckkit/record.py` executes a demo's real commands, keeps
their actual output and elapsed time, and renders the session as a terminal video in the
deck's own palette. Rendering rather than screen-capturing means the type size is chosen,
nothing else is in shot, and the video regenerates when a measurement moves. Long waits
are compressed with the true elapsed time printed on the frame.

**Verification** — the saved `.pptx` is read back and checked for missing motion, element
order, wrapped-height collisions, shapes outside the slide, banned language, required
sections, capitalisation, and any invariant the talk adds through an `extra=` hook.

## The worked examples

**`talks/bringing-the-model-home/`** — a 30-minute conference talk given at DevOpsDays
Cairo 2026, on running language models on a MacBook Air rather than a hosted API.
Eighteen slides, four embedded recordings, every measurement taken on the presenting
laptop.

**`talks/rosettacloud-genai-hackathon/`** — a 14-slide pitch deck answering a hackathon
upload specification. A rebranded palette, its own layout helper, no recordings. It
needed no change to the engine, which is the point of the split.

## Licence

The toolkit under `deckkit/` is MIT. Talk content and photographs are not.
