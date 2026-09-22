# The Agent Org — DevOps Hackathon Finals deck

**TD63 RosettaTeam · 26 September 2026 · Glass Room 1, 3:50 PM · Creativa Giza**

```zsh
.venv-deck/bin/python talks/devops-hackathon-final/build_deck.py
```

Builds `TheAgentOrg-Final.pptx` and verifies the saved file: motion, element order,
wrapped-height collisions, shape bounds, banned language, capitalisation, the six
required sections, and one talk-specific check that the gate slide precedes the demo
it explains.

| File | What it is |
|---|---|
| `TheAgentOrg-Final.pptx` | the deck — 14 slides plus 2 backup slides after the close |
| `REHEARSAL.md` | the speaking script, timings and prepared answers. Private |
| `DEMO-PLAN.md` | what the live demonstration shows. Suitable for organisers |
| `photos/square/` | five pre-cropped 640x640 portraits, reused from the pre-final deck |

## The clock

Twenty minutes covers the presentation, the demo AND the judges' questions.

```
slides      9:30    verified by the script in REHEARSAL.md
live demo   5:00    the poisoned run only
questions   5:30
```

Both runs live would be about ten minutes — measured, not estimated — so the clean
run is shown as a merged pull request that already exists.

## Every number is traceable

Each constant at the top of `build_deck.py` carries the command that produced it.
Re-run those before presenting; if one has moved, rebuild rather than correcting it
aloud.

## The two backup slides

They sit after the close and are shown only if asked: how a finding becomes a
verdict, and what the project does not do.
