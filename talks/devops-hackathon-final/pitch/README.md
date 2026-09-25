# The Agent Org — DevOps Hackathon Finals deck

**TD63 RosettaTeam · 26 September 2026 · Glass Room 1, 3:50 PM · Creativa Giza**

```zsh
.venv-deck/bin/python talks/devops-hackathon-final/build_deck.py
```

Builds `TheAgentOrg-Final.pptx` and verifies the saved file: motion, element order,
wrapped-height collisions, shape bounds, banned language, capitalisation, the six
required sections, and two talk-specific checks: the gate slide precedes the demo it
explains, and the deck opens with a speaker page and an agenda (see below).

| File | What it is |
|---|---|
| `TheAgentOrg-Final.pptx` | the deck — 18 slides |
| `../architecture/` | the AWS diagram: `make_architecture.py` writes `architecture.drawio` and renders `architecture.png` |
| `REHEARSAL.md` | the speaking script, timings and prepared answers. Private |
| `DEMO-PLAN.md` | what the live demonstration shows. Suitable for organisers |
| `photos/square/` | five pre-cropped 640x640 portraits, reused from the pre-final deck |

## The clock

Twenty minutes covers the presentation, the demo AND the judges' questions.

```
slides     10:50    verified by the script in REHEARSAL.md
live demo   5:00    the poisoned run only
questions   4:10
```

Both runs live would be about ten minutes — measured, not estimated — so the clean
run is shown as a merged pull request that already exists.

## Every number is traceable

Each constant at the top of `build_deck.py` carries the command that produced it.
Re-run those before presenting; if one has moved, rebuild rather than correcting it
aloud.

## The opening: a speaker page and an agenda

Slide 2 is RosettaTeam — each engineer's title and workplace, taken from the
pre-final deck. Slide 3 is the agenda — each section, one line on what it covers,
and its minutes. `_opening` in `build_deck.py` fails the build if either moves, if
the agenda omits a required section, or if its minutes do not fill the slot.

## The former backup slides are in the main flow

Scoring is slide 7, straight after the gate it explains; the judges asked for it by
name. The limits are slide 15, before the roadmap. That cost 0:50 of question time.

## The architecture diagram

```zsh
.venv-deck/bin/python talks/devops-hackathon-final/architecture/make_architecture.py
```

Needs draw.io desktop at `~/Applications/draw.io.app` (installed from the official
jgraph release; Homebrew's prefix on this machine belongs to another account). The
`.drawio` file opens in draw.io for hand edits; re-running the script overwrites it.
