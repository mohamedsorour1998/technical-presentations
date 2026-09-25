#!/usr/bin/env python3
"""Build The Agent Org's deck for the DevOps Hackathon FINAL, 26 September 2026.

    .venv-deck/bin/python talks/devops-hackathon-final/build_deck.py

Content only -- the engine is deckkit/deck.py.

THE CLOCK IS THE DESIGN CONSTRAINT. Twenty minutes covers the presentation, the
demo AND the judges' questions; the pre-final was thirty for the same three. So
this is seventeen slides in 10:20, a five-minute live demo of ONE blocked run, and
4:40 left for questions (pitch/REHEARSAL.md carries the per-slide sum). The demo ticket
is a REAL one, not the poisoned checkbox: it pins requests==2.19.0, and Trivy blocks it
on CVE-2018-18074 -- 81 s from approving gate1 to the block, rehearsed on run #73
(36096705514, 2026-09-25) with no demo flag set. A clean run with three approvals is
about six minutes -- both live would be half the slot.

THE BRIEF NAMES SIX SECTIONS and `_REQUIRED` asserts every one is present, so a
rewrite cannot silently drop one. Two of them -- BUSINESS IMPACT and
DIFFERENTIATION -- are new since the pre-final and were not enforced before.

EVERY FIGURE IS MEASURED AND CARRIES THE COMMAND THAT PRODUCED IT. Where a number
is a plan rather than a measurement it is tagged, because a judge who finds one
undeclared projection discounts every other number on the deck.

REGISTER. No source code on a slide, no per-person slides, no anthropomorphism, no
dramatised headings. All four are enforced by `verify()`; all four were violated by
an earlier draft of the pre-final deck.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from deckkit import deck, pages
from deckkit.deck import *  # noqa: F403 -- palette, geometry, primitives, build, verify

ROOT = pathlib.Path(__file__).resolve().parent
deck.VIDEO_DIR = ROOT / "pitch" / "video"

# ── palette — THE PRODUCT'S OWN, so the deck matches the app on screen ─────────
#
# Ported verbatim from `web/app/globals.css`, which is the palette the judges are
# about to see in the live demo. A deck in different colours from its own product
# reads as two projects.
#
# SET THROUGH deck.palette(), NEVER BY REASSIGNING THE IMPORTED NAMES. `import *`
# copies values; rebinding here would leave the engine's defaults in place and the
# deck would come out in two palettes at once -- which looks deliberate and so
# survives a read-through. `build()` refuses to run when it detects it.
#
# THE ACCENTS ARE THE PRODUCT'S AND WERE NOT RE-VALIDATED BY deckkit's CVD CHECK.
# Its measured figures (cyan vs dim dE 12.1 deutan; mint vs rose dE 7.7, marginal)
# were taken against the engine's own surface. Rather than assume they carry over,
# this deck honours the stricter half of that rule everywhere: EVERY mint or rose
# mark also carries a word, so a red/green colourblind viewer reads the label and
# never the hue.
deck.palette(
    VOID=RGBColor(0x07, 0x0A, 0x10),    # --surface-sunken
    SLATE=RGBColor(0x0B, 0x0F, 0x17),   # --surface
    RAISED=RGBColor(0x13, 0x1A, 0x25),  # --surface-raised
    TERM=RGBColor(0x07, 0x0A, 0x10),
    LINE=RGBColor(0x1F, 0x29, 0x37),    # --border
    INK=RGBColor(0xE8, 0xEC, 0xF3),     # --text
    DIM=RGBColor(0x8B, 0x97, 0xAB),     # --text-muted
    CYAN=RGBColor(0x22, 0xD3, 0xEE),    # --accent
    ROSE=RGBColor(0xFB, 0x71, 0x85),    # --refused
    MINT=RGBColor(0x6E, 0xE7, 0xB7),    # --shipped
)
VOID, SLATE, RAISED, TERM = deck.VOID, deck.SLATE, deck.RAISED, deck.TERM
LINE, INK, DIM = deck.LINE, deck.INK, deck.DIM
CYAN, MINT, ROSE = deck.CYAN, deck.MINT, deck.ROSE

# ── figures — each with the command that produced it, re-run 2026-09-22 ───────
PY_TESTS = 2182          # .venv-main/bin/python -m pytest --collect-only -q | tail -1   (2026-09-25, after ff2ac47)
PY_FILES = 96            # ls tests/test_*.py | wc -l   (2026-09-25, after ff2ac47)
WEB_TESTS = 338          # cd web && npm test   -> Tests 338 passed   (2026-09-25, after bf3a962)
WEB_FILES = 26           # ls web/{__tests__,lib/__tests__,components/__tests__}/*.ts | wc -l   (2026-09-25)
WORKFLOWS = 5            # ls .github/workflows/*.yml | wc -l
RUNTIME_VERSION = 56     # list-agent-runtimes: all five READY at 56, RETRIEVAL_ENABLED=true; preflight OK, LINES [3, 4]   (2026-09-25, after ff2ac47)

# docs/final/evidence/cost-comparison.md, three consecutive clean runs:
# $0.013036 and $0.016931. Shown in CENTS -- "$0.013–0.017" at 40pt wrapped onto its
# own label in a 3.4in column.
COST_CENTS = "1.3–1.7¢"
COST_LOW = "0.013"
COST_HIGH = "0.017"
COST_MEDIAN = "0.0131"   # $0.013102
INFRA_SHARE = "99.9"     # model share of marginal cost; infra was $0.0000125

# TheAgentOrg: scripts/measure_merge_history.py --refresh   (2026-09-25; was 8 of 37,
# 5.39 min and PR #50 on 2026-09-09 -- later runs waited on people, so the median rose)
MERGE_MEDIAN_MIN = "7.88"   # median of 12 ticket->merge times
MERGE_MAX_MIN = "2476.08"   # PR #58: its gates were clicked the next day
MERGES = 12
PIPELINE_RUNS = 57          # survivorship: 12 merges OF 57 runs. Stated on the slide.
ESCAPES = 0                 # credential escapes: 0 over 13 merged PRs, 12 of them the pipeline's
CONTROL_PR = 72             # the unmerged PR the same scan finds 3 in

# TheAgentOrg: .venv-main/bin/python scripts/measure_dependencies.py   (deabeef, 2026-09-24)
VENDOR_TOUCHING = 8      # modules touching a vendor SDK
VENDOR_MODULES = 2       # ...of which import it at load time
TOTAL_MODULES = 83

# preflight.py check 3, against the deployed security runtime
REAL_LINES = "3, 4"
FIXTURE_LINES = "4, 5"

# The demo ticket, rehearsed live 2026-09-25 on run #73 (36096705514), no demo flag:
# gate1 approved -> develop blocked, from GitHub's job timestamps.
BLOCK_SECONDS = "81 s"

_REQUIRED = (
    "OVERVIEW", "BUSINESS IMPACT", "DIFFERENTIATION",
    "ARCHITECTURE", "PROGRESS", "FUTURE WORK",
)

# Anthropomorphism and dramatisation, plus the superlatives a pitch deck reaches
# for by reflex. All enforced against the SAVED file.
_BANNED = (
    r"\bit lied\b", r"\bknows\b", r"\bwants to\b", r"\btried to\b", r"\bunderstands\b",
    r"\brevolutionary\b", r"\bgame.?chang", r"\bcutting.?edge\b", r"\bdisrupt",
    r"\bworld.?class\b", r"\bsynerg", r"\bseamless\b", r"\bnobody noticed\b",
)

# The speaker page. Titles and workplaces are copied from the pre-final deck
# (TheAgentOrg/scripts/make_deck.py, TEAM) so the two decks cannot disagree about
# who anybody is. `extra` is one more line, used for one person only.
TEAM = [
    pages.Person("sorour.jpg", "Mohamed Sorour", "Senior DevOps Engineer", "VEZEETA",
                 "AWS Community Builder\nMSc student\nComputer Science\nAI specialization\nGeorgia Tech"),
    pages.Person("mariam.jpg", "Mariam Abdelkader", "Associate Solution Engineer", "RENOSYSTEMS"),
    pages.Person("habiba.jpg", "Habiba Megahed", "Junior DevOps Engineer", "DIGILIANS ALUM"),
    pages.Person("reem.jpg", "Reem Shkeep", "Junior Testing Engineer", "DIGILIANS ALUM"),
    pages.Person("aya.jpg", "Aya Ebrahim", "Junior Testing Engineer", "DIGILIANS ALUM"),
]

# The agenda. Minutes are pitch/REHEARSAL.md's timings rounded, and they must
# sum to the slot: 20 minutes including the demo and the judges' questions.
AGENDA = [
    pages.Section("Overview", "the problem, the pipeline, the gate, and what the agents read", 4),
    pages.Section("Architecture", "what runs where, on AWS and on GitHub", 1),
    pages.Section("Business impact", "what a change costs, and what it buys", 1),
    pages.Section("Differentiation", "what vendors say about their own AI review", 1),
    pages.Section("Progress", "what is built, your ten notes, and what it does not do", 2),
    pages.Section("Future work", "what is next", 1),
    pages.Section("Live demonstration", "a ticket that pins a vulnerable library, refused", 5),
    pages.Section("Questions", "the rest of the slot is yours", 4),
]
SLOT_MINUTES = 20
OPENING_MINUTES = 1        # title, team and agenda -- spoken, not listed

STAGES = ["plan", "gate1", "develop", "review", "security", "gate2", "sre", "gate3", "promote"]
GATES = {"gate1", "gate2", "gate3"}


# ── talk-local helpers ────────────────────────────────────────────────────────

def _spine(slide, *, top, stopped_after=None):
    """The nine stages: a gate is a RING, an agent stage a filled dot.

    ONE COLOUR ON THE OVERVIEW. Shape tells a gate from a stage; a second hue added
    nothing but a question. On the demo slide colour carries state and nothing else:
    cyan for a stage that ran, rose for the one that stopped the run, a hairline for
    the stages that never started.
    """
    shapes = []
    n = len(STAGES)
    width = BODY_W / n
    for index, name in enumerate(STAGES):
        x = MARGIN + width * index
        gate = name in GATES
        dead = stopped_after is not None and index > stopped_after
        blocked = stopped_after is not None and index == stopped_after
        colour = ROSE if blocked else (LINE if dead else CYAN)
        cx = x + width / 2
        size = Inches(0.19) if gate else Inches(0.13)
        mark = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - size / 2, top, size, size)
        mark.fill.solid()
        mark.fill.fore_color.rgb = SLATE if gate else colour
        mark.line.color.rgb = colour
        mark.line.width = Pt(2)
        mark.shadow.inherit = False
        shapes.append(mark)
        if index < n - 1:
            after_dead = stopped_after is not None and index >= stopped_after
            rail = slide.shapes.add_shape(1, cx + size / 2, top + size / 2 - Inches(0.01),
                                          width - size, Inches(0.02))
            rail.fill.solid()
            rail.fill.fore_color.rgb = LINE if after_dead else CYAN
            rail.line.fill.background()
            rail.shadow.inherit = False
        shapes.append(textbox(slide, name, left=x, top=top + Inches(0.34), width=width,
                              height=Inches(0.3), size=11, color=DIM if dead else INK,
                              font=MONO, align=PP_ALIGN.CENTER, spacing=1.0))
    return shapes


def _rowcards(slide, items, *, top, height=Inches(1.55), gap=Inches(0.26), size=13):
    """A row of equal-width cards. `items` is [(title, body), ...]."""
    n = len(items)
    width = (BODY_W - gap * (n - 1)) / n
    shapes = []
    x = MARGIN
    for title, body in items:
        card = slide.shapes.add_shape(1, x, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = RAISED
        card.line.color.rgb = LINE
        card.line.width = Pt(1)
        card.shadow.inherit = False
        shapes.append(card)
        shapes.append(textbox(slide, title, left=x + Inches(0.2), top=top + Inches(0.16),
                              width=width - Inches(0.4), height=Inches(0.56), size=14,
                              color=CYAN, bold=True, spacing=1.1))
        shapes.append(textbox(slide, body, left=x + Inches(0.2), top=top + Inches(0.74),
                              width=width - Inches(0.4), height=height - Inches(0.9),
                              size=size, color=DIM, spacing=1.3))
        x += width + gap
    return shapes


def _numbered(slide, items, *, top=Inches(2.3), step=Inches(1.12)):
    """Numbered rows -- number, a bold title, one or two lines of detail. Used by the
    limits and the roadmap so the two read as a pair."""
    heads, y = [], top
    for index, (title, detail) in enumerate(items, start=1):
        heads.append(textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.7),
                             height=Inches(0.4), size=15, color=CYAN, bold=True, font=MONO))
        heads.append(textbox(slide, title, left=Inches(1.9), top=y, width=Inches(4.3),
                             height=Inches(0.7), size=16, color=INK, bold=True, spacing=1.15))
        textbox(slide, detail, left=Inches(6.4), top=y, width=Inches(5.8),
                height=Inches(1.0), size=14, color=DIM, spacing=1.3)
        y += step
    return heads


# ── slides ────────────────────────────────────────────────────────────────────

def slide_title(prs):
    """THE PROJECT'S NAME IS THE TITLE. The first version led with the tagline and set
    the name in 12pt beneath it; a reviewer asked where the project's name was."""
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "The Agent Org", left=MARGIN, top=Inches(1.55), width=BODY_W,
            height=Inches(1.1), size=60, color=INK, bold=True, spacing=1.0)
    rule(slide, top=Inches(2.85), width=Inches(2.6), color=CYAN)
    textbox(slide, "Security gates for agent-written code", left=MARGIN, top=Inches(3.15),
            width=BODY_W, height=Inches(0.6), size=28, color=CYAN, spacing=1.0)
    textbox(slide,
            "Five agents take a ticket to a pull request. Three human gates and one "
            "deterministic rule decide whether it ships.",
            left=MARGIN, top=Inches(4.05), width=Inches(10.6), height=Inches(0.9),
            size=20, color=DIM, spacing=1.35)
    textbox(slide,
            "DevOps Hackathon Finals 2026 · TD63 RosettaTeam\n"
            + " · ".join(person.name for person in TEAM),
            left=MARGIN, top=Inches(5.95), width=BODY_W, height=Inches(0.8), size=14,
            color=DIM, spacing=1.4)
    transition(slide, kind="fade")


def slide_problem(prs):
    """OVERVIEW, first half — the problem, stated as a measurement."""
    slide = new_slide(prs)
    heading(slide, "An agent can write the code. Who checks it?", kicker="overview", size=32)
    body = bullets(slide, [
        "Coding agents now open pull requests without a person in the loop. "
        "The reviewer of that change is increasingly another model.",
        "A model can be persuaded, distracted or prompt-injected. It is the wrong "
        "thing to place between a committed credential and the main branch.",
        "Measured on this project's own baseline: with no checks in the loop, "
        "a poisoned change reached the branch every time it was tried.",
    ], top=Inches(2.5), size=18, gap=0.92)
    note = textbox(slide,
                   "The question is not whether an agent can write the change. "
                   "It is what stands between that change and production.",
                   left=MARGIN, top=Inches(5.9), width=Inches(11.0), height=Inches(0.9),
                   size=18, color=INK, bold=True, spacing=1.3)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [note.shape_id])


def slide_solution(prs):
    """OVERVIEW, second half — the pipeline, in the shape the demo will show."""
    slide = new_slide(prs)
    heading(slide, "Nine stages. Three of them are people.", kicker="overview", size=32)
    marks = _spine(slide, top=Inches(2.5))
    legend = textbox(slide,
                     "A filled dot is an agent. A ring is a gate: the pipeline stops there "
                     "until a named person approves it.",
                     left=MARGIN, top=Inches(3.35), width=Inches(11.0), height=Inches(0.7),
                     size=15, color=DIM, spacing=1.3)
    cards = _rowcards(slide, [
        ("Five agents",
         "planner, developer, reviewer, security and SRE, each in its own isolated "
         "runtime on AWS."),
        ("Three human gates",
         "a required reviewer in GitHub. The run waits at each gate until a named "
         "person approves it."),
        ("One rule that is not a model",
         "three scanners and a fixed severity threshold. Same input, same answer, "
         "every time."),
    ], top=Inches(4.25), height=Inches(2.0))
    transition(slide)
    animate(slide, [s.shape_id for s in marks if s.has_text_frame]
            + [legend.shape_id] + [s.shape_id for s in cards if s.has_text_frame])


def slide_gate(prs):
    """OVERVIEW — the core argument. Determinism on top of non-determinism."""
    slide = new_slide(prs)
    heading(slide, "Non-deterministic models. A deterministic gate.",
            kicker="overview", size=30)
    textbox(slide,
            "Every agent here is a language model, and any of them can be wrong. "
            "The component that stops a change is not one of them.",
            left=MARGIN, top=Inches(2.3), width=Inches(11.0), height=Inches(0.75),
            size=17, color=DIM, spacing=1.3)
    table(slide, ["", "the reviewer", "the security stage"],
          [["what it is", "a model reading the change", "three scanners and a fixed rule"],
           ["what it catches", "intent, logic, a plan mismatch", "credentials, known CVEs, unsafe code"],
           ["its authority", "advisory: it sends the change back", "binding: it stops the run"],
           ["same input twice", "may answer differently", "the same answer, always"],
           ["can be talked out of it", "yes, it reads a prompt", "no, no model takes part in the decision"]],
          top=Inches(3.2), left=MARGIN, height=0.5,
          widths=[Inches(2.7), Inches(4.2), Inches(4.2)], size=15, mono=False)
    note = textbox(slide,
                   "The block is built into the pipeline, not added as a status check: when "
                   "security refuses, its job fails and the next gate cannot start.",
                   left=MARGIN, top=Inches(6.2), width=Inches(11.0), height=Inches(0.7),
                   size=15, color=INK, spacing=1.3)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_architecture(prs):
    """ARCHITECTURE — the AWS reference-architecture diagram from
    architecture/make_architecture.py, full slide under a compact head."""
    pages.diagram_page(prs, ROOT / "architecture" / "architecture.png",
                       kicker="architecture", heading_text="What runs where — follow the numbers")


def slide_impact(prs):
    """BUSINESS IMPACT — stated without overreach."""
    slide = new_slide(prs)
    heading(slide, "What it costs, and what it buys", kicker="business impact", size=32)
    figs = figure(slide, COST_CENTS, "model cost per change\nthree measured runs",
                  left=MARGIN, top=Inches(2.35), width=Inches(3.4), color=CYAN)
    figs += figure(slide, f"{MERGE_MEDIAN_MIN} min", f"median ticket to merge\n{MERGES} merges",
                   left=Inches(4.8), top=Inches(2.35), width=Inches(3.4), color=CYAN)
    figs += figure(slide, f"{ESCAPES} of {MERGES}", "merged changes carrying\na credential",
                   left=Inches(8.4), top=Inches(2.35), width=Inches(3.4), color=CYAN)
    body = bullets(slide, [
        f"The model is {INFRA_SHARE}% of what a change costs. Lambda, EventBridge and "
        "DynamoDB together came to twelve millionths of a dollar. The only cost work "
        "worth doing is prompt caching.",
        "The value is not the cents. A credential cannot reach the main branch by being "
        "approved quickly, and that refusal has no model in it.",
    ], top=Inches(4.45), size=16, gap=0.95)
    caveat = textbox(slide,
                     f"{MERGES} of {PIPELINE_RUNS} runs merged, so the median covers the runs "
                     f"that finished. The same scan finds 3 credentials in unmerged pull "
                     f"request #{CONTROL_PR}, so the zero is a real result.",
                     left=MARGIN, top=Inches(6.35), width=Inches(11.0), height=Inches(0.7),
                     size=13, color=DIM, spacing=1.25)
    transition(slide)
    animate(slide, [s.shape_id for s in figs] + [s.shape_id for s in body] + [caveat.shape_id])


def slide_differentiation(prs):
    """DIFFERENTIATION — their own words first."""
    slide = new_slide(prs)
    heading(slide, "Every vendor's AI review is advisory. They say so.",
            kicker="differentiation", size=28)
    table(slide, ["product", "from their own documentation"],
          # RE-READ 2026-09-25: GitHub rewrote this page. "will not block merging changes"
          # is gone, and approvals are now an opt-in -- so the row quotes what is there.
          [["GitHub Copilot review", "by default “a ‘Comment’ review, not … a ‘Request changes’ review”"],
           ["Anthropic Code Review", "“always completes with a neutral conclusion so it never blocks merging”"],
           ["OpenAI Codex", "“don't replace tests, branch protections, or required approvals”"],
           ["Cursor Bugbot", "findings “default to neutral”"],
           ["Snyk", "“The generator cannot be the validator.”"]],
          top=Inches(2.35), left=MARGIN, height=0.48,
          widths=[Inches(3.3), Inches(7.8)], size=15, mono=False)
    note = textbox(slide,
                   "Some vendors do enforce rules outside the model: Claude Code's permission "
                   "rules, Factory's commit blocks. The difference is where the check sits. "
                   "Theirs guard one agent's actions; ours guards the hand-off between "
                   "agents, with a named person approving each stage.",
                   left=MARGIN, top=Inches(5.45), width=Inches(11.0), height=Inches(1.3),
                   size=16, color=INK, spacing=1.3)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_failopen(prs):
    """DIFFERENTIATION, second beat — their failure mode is our design in reverse.
    Plain words, not exit codes: "exit 2 denies" meant nothing to a reviewer."""
    slide = new_slide(prs)
    heading(slide, "When their check breaks, the change goes through",
            kicker="differentiation", size=30)
    cards = _rowcards(slide, [
        ("Cursor hooks",
         "If a hook itself fails, the action goes ahead. Their documentation calls it "
         "“fail-open by default”."),
        # VERBATIM, re-read 2026-09-25. The card used to put a paraphrase in quote
        # marks; the documentation's sentence is longer and is the one quoted now.
        ("Claude Code hooks",
         "Only one specific failure blocks; any other lets the action through. Their "
         "documentation: “a mistyped path in settings.json leaves the gate silently "
         "disabled”."),
        # "By default": `semgrep ci` passes on internal errors unless run with
        # --no-suppress-errors. Their words: it "returns exit code 0".
        ("Semgrep",
         "By default, if the scanner crashes it still reports success, so a crash "
         "reads like a clean scan."),
    ], top=Inches(2.45), height=Inches(2.55), size=14)   # 2.2 -- the verbatim quote ran past the card
    note = textbox(slide,
                   "A check that did not run, reading as a check that passed. That is the "
                   "failure this project is built to refuse: in our pipeline a missing or "
                   "crashed scanner blocks the change.",
                   left=MARGIN, top=Inches(5.15), width=Inches(11.0), height=Inches(1.2),
                   size=18, color=INK, spacing=1.35)
    transition(slide)
    animate(slide, [s.shape_id for s in cards if s.has_text_frame] + [note.shape_id])


def slide_progress(prs):
    """PROGRESS — what exists, measured today."""
    slide = new_slide(prs)
    heading(slide, "What is built", kicker="progress", size=32)
    figs = figure(slide, f"{PY_TESTS}", f"automated tests\nacross {PY_FILES} files",
                  left=MARGIN, top=Inches(2.35), width=Inches(3.4), color=CYAN)
    figs += figure(slide, f"{WEB_TESTS}", f"more for the web app\nacross {WEB_FILES} files",
                   left=Inches(4.8), top=Inches(2.35), width=Inches(3.4), color=CYAN)
    figs += figure(slide, f"v{RUNTIME_VERSION}", "five agent runtimes\nall ready, one version",
                   left=Inches(8.4), top=Inches(2.35), width=Inches(3.4), color=CYAN)
    cards = _rowcards(slide, [
        ("Running in the cloud",
         "An issue triggers a Lambda, an event bus starts the pipeline, five runtimes "
         "answer, and three gates wait for a person."),
        ("A product, not a script",
         "Sign in, pick a repository, start a run, watch each stage, approve a gate, "
         "read the cost."),
        ("Multi-tenant",
         "Each customer's data sits in its own partition, and AWS itself refuses a "
         "read of anyone else's."),
    ], top=Inches(4.35), height=Inches(2.05))
    transition(slide)
    animate(slide, [s.shape_id for s in figs] + [s.shape_id for s in cards if s.has_text_frame])


def slide_knowledge(prs):
    """OVERVIEW — the knowledge base, closing the section: what the agents read, and that
    it never reaches the rule the two slides before it explained.

    Every figure is measured: 8/8 vs 6/8 and 0/40 by `agentorg.retrieval.measure`, 18
    documents on the saved state of run #75 (36116159979) -- the first deployed run
    with RETRIEVAL_ENABLED on, 2026-09-25. Before that it was wired and switched off.
    """
    slide = new_slide(prs)
    heading(slide, "What the agents read before they answer",
            kicker="overview · knowledge base", size=30)
    figs = figure(slide, "8/8", "plan mismatches caught\nwith it — 6/8 without",
                  left=MARGIN, top=Inches(2.35), width=Inches(3.4), color=CYAN)
    figs += figure(slide, "0/40", "false blocks, with it\nor without it",
                   left=Inches(4.8), top=Inches(2.35), width=Inches(3.4), color=CYAN)
    figs += figure(slide, "18", "documents read on one\nlive run, in production",
                   left=Inches(8.4), top=Inches(2.35), width=Inches(3.4), color=CYAN)
    cards = _rowcards(slide, [
        ("Past rejections",
         "Why earlier changes to this app were sent back, so the developer does not "
         "repeat a mistake."),
        ("Team conventions",
         "Questions the team has already settled, so the reviewer stops arguing them "
         "again."),
        ("Security advisories",
         "Background on known vulnerabilities, so the security explanation is "
         "specific."),
    ], top=Inches(4.35), height=Inches(1.8))
    caveat = textbox(slide,
                     "Four agents read it: planner, developer, reviewer and the security "
                     "explanation. Keyword search, no vector database. It shapes wording, "
                     "never the verdict: five hostile documents were planted, and the block "
                     "did not move.",
                     left=MARGIN, top=Inches(6.3), width=Inches(11.0), height=Inches(0.75),
                     size=13, color=DIM, spacing=1.25)
    transition(slide)
    animate(slide, [s.shape_id for s in figs] + [s.shape_id for s in cards if s.has_text_frame]
            + [caveat.shape_id])


def slide_notes(prs):
    """PROGRESS — the pre-final feedback, answered, row for row."""
    slide = new_slide(prs)
    heading(slide, "Your ten notes from the pre-final", kicker="progress", size=30)
    table(slide, ["what you asked for", "what exists now"],
          [["Evaluation criteria", "measured before and after: plan-mismatch catches went 6/8 → 8/8"],
           ["Time and cost vs a coding agent", f"{COST_CENTS} of model time per change, priced from the AWS Pricing API"],
           ["External dependency", f"{VENDOR_TOUCHING} of {TOTAL_MODULES} modules touch a vendor SDK; {VENDOR_MODULES} load one at start-up"],
           ["Self-hosted", "one compose file runs the web app, the API, the worker and a local model"],
           ["Competitive advantage", "commissioned research, which disproved five of our own claims"],
           ["Scanner scoring → go / no-go", "one scoring table for all three scanners, built because of this note"],
           ["Generated tests + Selenium", "an agent writes tests from the ticket; Selenium runs in CI"],
           ["RAG / knowledge lake", "three curated knowledge bases, used by four of the agents"],
           ["A real UI", "sign-in, a live view of each run, gate approval, and cost"],
           ["Restructure as SaaS", "multi-tenant, with a control-plane API and per-tenant isolation"]],
          top=Inches(2.3), left=MARGIN, height=0.42,
          widths=[Inches(3.8), Inches(7.3)], size=13, mono=False)
    transition(slide)


def slide_roadmap(prs):
    """FUTURE WORK — the first item is the gap the limits slide names, in the same
    layout, so the two read as one argument. No "[NEXT]" tags: the order says it."""
    slide = new_slide(prs)
    heading(slide, "What is next", kicker="future work", size=32)
    heads = _numbered(slide, [
        ("Apply the change, not just carry it",
         "Today a merged pull request carries the reviewed diff as a file. Applying it to "
         "the source is next, and lets a generated test run against the change."),
        ("Join the two test layers",
         "Tests are generated from each ticket and Selenium runs in CI; neither checks "
         "the other yet."),
        ("Prompt caching",
         "Nothing is cached today: every agent re-sends the same repository snapshot at "
         "full price. Cached input costs a quarter as much."),
        ("More languages, more scanners",
         "One Python target and three scanners today. The scoring is a table, so a new "
         "scanner is one row."),
    ])
    transition(slide)
    animate(slide, [s.shape_id for s in heads])


def slide_demo(prs):
    """The handover. A holding slide, so the screen is not a dead deck."""
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "The demonstration", left=MARGIN, top=Inches(2.0), width=BODY_W,
            height=Inches(0.9), size=44, color=INK, bold=True)
    rule(slide, top=Inches(3.1), width=Inches(2.2), color=CYAN)
    marks = _spine(slide, top=Inches(3.7), stopped_after=4)
    textbox(slide,
            "A real ticket: pin an old version of a library for a legacy system. Nothing is "
            "planted and no demo flag is set. Trivy finds a known vulnerability, the run "
            "stops at the security stage, and nothing after it runs.",
            left=MARGIN, top=Inches(4.6), width=Inches(11.0), height=Inches(0.8),
            size=17, color=DIM, spacing=1.3)
    textbox(slide,
            "Watch the threshold: the high-severity finding stops the run, and the medium "
            "ones do not. The same comparison, per scanner, is on the screen.",
            left=MARGIN, top=Inches(5.6), width=Inches(11.0), height=Inches(0.8),
            size=15, color=INK, spacing=1.3)
    transition(slide, kind="fade")
    animate(slide, [s.shape_id for s in marks if s.has_text_frame])


def slide_team(prs):
    """THE SPEAKER PAGE — second slide, before the agenda. No closing sentence: the one
    that stood here ("fourteen parallel workstreams") raised more questions than it
    answered."""
    pages.speaker_page(prs, TEAM, photo_dir=ROOT / "pitch" / "photos" / "square",
                       heading_text="RosettaTeam", kicker="the team · TD63")


def slide_agenda(prs):
    """THE AGENDA — third slide, so the room stops tracking whether a topic is coming."""
    pages.agenda_page(prs, AGENDA, heading_text="Twenty minutes, in this order")


def slide_close(prs):
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "Thank you", left=MARGIN, top=Inches(2.35), width=BODY_W,
            size=48, color=INK, bold=True)
    rule(slide, top=Inches(3.5), width=Inches(2.2), color=CYAN)
    textbox(slide, "Questions", left=MARGIN, top=Inches(4.0), width=Inches(6.0),
            height=Inches(0.65), size=28, color=CYAN, bold=True)
    textbox(slide,
            "theagentorg.rosettacloud.app\n"
            "DevOps Hackathon Finals 2026 · TD63 RosettaTeam",
            left=MARGIN, top=Inches(6.1), width=BODY_W, size=15, color=DIM, spacing=1.4)
    transition(slide, kind="fade")


def slide_scoring(prs):
    """OVERVIEW — the scoring, right after the gate it explains. Every sentence here is
    checked against TheAgentOrg's agentorg/security/scoring.py."""
    slide = new_slide(prs)
    heading(slide, "How a finding becomes a verdict", kicker="overview · scoring", size=30)
    table(slide, ["scanner", "how its severity is decided"],
          [["Semgrep", "its own severity, translated through one table"],
           ["Trivy", "its own severity, translated through the same table"],
           ["gitleaks", "it reports no severity, so every secret is critical, by policy"]],
          top=Inches(2.35), left=MARGIN, height=0.5,
          widths=[Inches(2.6), Inches(8.5)], size=15, mono=False)
    body = bullets(slide, [
        "One comparison decides: block when any finding is at or above the threshold.",
        "A severity the table does not recognise counts as high, the blocking level, so "
        "an unknown can never pass.",
        "A secret is always critical, so no threshold setting lets a committed "
        "credential through.",
        "A threshold outside the allowed values is rejected, never quietly adjusted.",
    ], top=Inches(4.55), size=16, gap=0.62)
    transition(slide)
    animate(slide, [s.shape_id for s in body])


def slide_limits(prs):
    """PROGRESS — the limits, BEFORE the roadmap, in the roadmap's own layout."""
    slide = new_slide(prs)
    heading(slide, "What this does not do", kicker="progress · limits", size=30)
    heads = _numbered(slide, [
        ("An admin can bypass a gate",
         "A repository setting, not a code path. Our pre-flight check reports it on "
         "every run."),
        ("The reviewer is advisory",
         "If the scanners miss something, only the reviewer saw it, and it cannot stop "
         "the run. The human gates are the last line."),
        ("One language, three scanners",
         "One Python target today. Breadth is where every competitor is ahead."),
        ("The change is carried, not applied",
         "A merged pull request carries the reviewed diff as a file. Applying it to the "
         "source is next."),
    ])
    transition(slide)
    animate(slide, [s.shape_id for s in heads])


SLIDES = [
    slide_title, slide_team, slide_agenda,
    slide_problem, slide_solution, slide_gate, slide_scoring, slide_knowledge,
    slide_architecture,
    slide_impact,
    slide_differentiation, slide_failopen,
    slide_progress, slide_notes, slide_limits,
    slide_roadmap,
    slide_demo, slide_close,
]
# No entrance animation on: title, agenda (read at once), architecture (one
# image), the ten notes (a table read at once), and close.
_STATIC = 5


def _exposition_order(path, slides, text) -> list[str]:
    """THE GATE MUST BE EXPLAINED BEFORE THE DEMO THAT RELIES ON IT.

    `slide_gate` establishes that the blocking component contains no model. The
    demo slide then asks the room to read a block as the design working rather
    than as a crash. Presented the other way round, the audience meets an
    unexplained refusal and the explanation arrives as a justification.
    """
    names = [fn.__name__ for fn in slides]
    problems = []
    if names.index("slide_gate") > names.index("slide_demo"):
        problems.append("slide_gate must precede slide_demo: the demo relies on it")
    if names.index("slide_problem") > names.index("slide_solution"):
        problems.append("slide_problem must precede slide_solution")
    # ANTI-VACUITY: if either name is renamed this check silently stops applying.
    if "slide_gate" not in names or "slide_demo" not in names:
        problems.append("the exposition check found neither slide; it is pinning nothing")
    return problems


SCRIPT = ROOT / "pitch" / "REHEARSAL.md"


def main() -> int:
    out = build(SLIDES, ROOT / "pitch" / "TheAgentOrg-Final.pptx")
    # Speaker notes come from the rehearsal script, so Presenter View shows exactly
    # what was rehearsed; notes_check fails the build if the two drift apart.
    add_notes(out, {n: notes for n, (_title, notes) in pages.rehearsal(SCRIPT).items()})
    code = verify(out, SLIDES, required=_REQUIRED, banned=_BANNED, static=_STATIC,
                  extra=[_exposition_order,
                         pages.opening_check(AGENDA, required=_REQUIRED, slot_minutes=SLOT_MINUTES,
                                             opening_minutes=OPENING_MINUTES),
                         pages.notes_check(SCRIPT)])
    kind = subprocess.run(["file", "-b", str(out)], capture_output=True, text=True,
                          check=False).stdout.strip()
    print(f"  file(1):     {kind}")
    return code


if __name__ == "__main__":
    sys.exit(main())
