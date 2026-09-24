#!/usr/bin/env python3
"""Build The Agent Org's deck for the DevOps Hackathon FINAL, 26 September 2026.

    .venv-deck/bin/python talks/devops-hackathon-final/build_deck.py

Content only -- the engine is deckkit/deck.py.

THE CLOCK IS THE DESIGN CONSTRAINT. Twenty minutes covers the presentation, the
demo AND the judges' questions; the pre-final was thirty for the same three. So
this is twelve slides at roughly forty-five seconds, a five-minute live demo of
the poisoned run only, and the rest left for questions. Measured: the poisoned run
is 2m19s from approving gate1 to the block (run 35679536930) and a clean run with
three approvals is about six minutes -- both live would be half the slot.

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

from deckkit import deck
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
PY_TESTS = 2172          # .venv-main/bin/python -m pytest --collect-only -q | tail -1   (2026-09-24)
PY_FILES = 93            # ls tests/test_*.py | wc -l
WEB_TESTS = 311          # cd web && npx vitest run   -> Tests 311 passed
WEB_FILES = 24           # ls web/{__tests__,lib/__tests__,components/__tests__}/*.ts | wc -l
WORKFLOWS = 5            # ls .github/workflows/*.yml | wc -l
RUNTIME_VERSION = 54     # scripts/preflight.py check 2   (2026-09-24, all five READY)

# docs/final/evidence/cost-comparison.md, three consecutive clean runs
COST_LOW = "0.013"       # $0.013036
COST_HIGH = "0.017"      # $0.016931
COST_MEDIAN = "0.0131"   # $0.013102
INFRA_SHARE = "99.9"     # model share of marginal cost; infra was $0.0000125

# docs/final/evidence/merge-history.json, computed 2026-09-22
MERGE_MEDIAN_MIN = "5.39"   # median of 8 ticket->merge times
MERGE_MAX_MIN = "27.07"
MERGES = 8
PIPELINE_RUNS = 37          # survivorship: 8 merges OF 37 runs. Stated on the slide.
ESCAPES = 0                 # credential escapes over the 8 merged PRs
CONTROL_PR = 50             # the unmerged PR the same scan finds 3 in

# scripts/measure_dependencies.py — AST, not grep
VENDOR_MODULES = 1
TOTAL_MODULES = 50

# preflight.py check 3, against the deployed security runtime
REAL_LINES = "3, 4"
FIXTURE_LINES = "4, 5"

# The live poisoned run, 2026-09-22 — run 35679536930
BLOCK_SECONDS = "2 min 19 s"

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
# who anybody is. The fourth field is one extra line, used for one person only.
TEAM = [
    ("sorour.jpg", "Mohamed Sorour", "Senior DevOps Engineer", "VEZEETA",
     "Aiming for an MSc in Computer Science, AI specialization · Georgia Tech"),
    ("mariam.jpg", "Mariam Abdelkader", "Associate Solution Engineer", "RENOSYSTEMS", ""),
    ("habiba.jpg", "Habiba Megahed", "Junior DevOps Engineer", "DIGILIANS ALUM", ""),
    ("reem.jpg", "Reem Shkeep", "Junior Testing Engineer", "DIGILIANS ALUM", ""),
    ("aya.jpg", "Aya Ebrahim", "Junior Testing Engineer", "DIGILIANS ALUM", ""),
]

# The agenda. Minutes are pitch/REHEARSAL.md's timings rounded, and they must
# sum to the slot: 20 minutes including the demo and the judges' questions.
AGENDA = [
    ("Overview", "the problem, the pipeline, and why the gate is not a model", 3),
    ("Architecture", "what runs where, on AWS and on GitHub", 1),
    ("Business impact", "what a change costs, and what it buys", 1),
    ("Differentiation", "what vendors say about their own AI review", 1),
    ("Progress", "what is built, your ten notes, and what it does not do", 2),
    ("Future work", "what is next", 1),
    ("Live demonstration", "a ticket that carries a credential, refused", 5),
    ("Questions", "the rest of the slot is yours", 5),
]
SLOT_MINUTES = 20
OPENING_MINUTES = 1        # title, team and agenda -- spoken, not listed

STAGES = ["plan", "gate1", "develop", "review", "security", "gate2", "sre", "gate3", "promote"]
GATES = {"gate1", "gate2", "gate3"}


# ── talk-local helpers ────────────────────────────────────────────────────────

def _chip(slide, text, *, left, top, width, height=Inches(0.52), colour=None,
          fill=None, size=12):
    """A bordered label. The architecture slides are built from these."""
    box = slide.shapes.add_shape(1, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = fill or RAISED
    box.line.color.rgb = colour or LINE
    box.line.width = Pt(1)
    box.shadow.inherit = False
    textbox(slide, text, left=left, top=top + Inches(0.12), width=width,
            height=height - Inches(0.16), size=size, color=colour or INK,
            font=MONO, align=PP_ALIGN.CENTER, spacing=1.0)
    return box


def _spine(slide, *, top, stopped_after=None):
    """The nine stages as the product draws them: a gate is a RING, a stage a dot.

    Mirrors `web/components/StageSpine.tsx` deliberately -- the judges see this
    shape in the live demo thirty seconds later, and a diagram that disagrees with
    the running product is worse than no diagram.
    """
    shapes = []
    n = len(STAGES)
    width = BODY_W / n
    for index, name in enumerate(STAGES):
        x = MARGIN + width * index
        dead = stopped_after is not None and index > stopped_after
        colour = ROSE if (stopped_after is not None and index == stopped_after) else (
            LINE if dead else MINT)
        cx = x + width / 2
        size = Inches(0.19) if name in GATES else Inches(0.13)
        mark = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - size / 2, top, size, size)
        mark.fill.solid()
        # A GATE IS HOLLOW: a decision a person makes is a different kind of thing
        # from a step that ran, and the product draws the same distinction.
        mark.fill.fore_color.rgb = SLATE if name in GATES else colour
        mark.line.color.rgb = colour
        mark.line.width = Pt(2)
        mark.shadow.inherit = False
        shapes.append(mark)
        if index < n - 1:
            rail = slide.shapes.add_shape(1, cx + size / 2, top + size / 2 - Inches(0.01),
                                          width - size, Inches(0.02))
            rail.fill.solid()
            rail.fill.fore_color.rgb = LINE if dead else colour
            rail.line.fill.background()
            rail.shadow.inherit = False
        shapes.append(textbox(slide, name, left=x, top=top + Inches(0.34), width=width,
                              height=Inches(0.3), size=11,
                              color=DIM if dead else (INK if name not in GATES else CYAN),
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


# ── slides ────────────────────────────────────────────────────────────────────

def slide_title(prs):
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "SECURITY GATES FOR\nAGENT-WRITTEN CODE", left=MARGIN, top=Inches(1.6),
            width=BODY_W, height=Inches(1.8), size=48, color=INK, bold=True, spacing=1.04)
    rule(slide, top=Inches(3.6), width=Inches(2.6), color=CYAN)
    textbox(slide,
            "Five agents take a ticket to a pull request. Three human gates and one "
            "deterministic rule decide whether it ships.",
            left=MARGIN, top=Inches(4.0), width=Inches(10.6), size=20, color=DIM, spacing=1.35)
    textbox(slide, "THE AGENT ORG", left=MARGIN, top=Inches(5.7), width=Inches(6),
            height=Inches(0.4), size=12, color=CYAN, bold=True, font=MONO, spacing=1.0)
    textbox(slide,
            "DevOps Hackathon Finals 2026 · TD63 RosettaTeam\n"
            "Mohamed Sorour · Mariam · Habiba · Reem · Aya",
            left=MARGIN, top=Inches(6.15), width=BODY_W, size=14, color=DIM, spacing=1.4)
    transition(slide, kind="fade")


def slide_problem(prs):
    """OVERVIEW, first half — the problem, stated as a measurement."""
    slide = new_slide(prs)
    heading(slide, "An agent can write the code. Who checks it?", kicker="overview", size=32)
    body = bullets(slide, [
        "Coding agents now open pull requests without a person in the loop. "
        "The reviewer of that change is increasingly another model.",
        "A model can be persuaded, distracted or prompt-injected. It is the wrong "
        "thing to place between a committed credential and a default branch.",
        "Measured on this project's own baseline: with no checks in the loop, "
        "a poisoned change reached the branch every time it was tried.",
    ], top=Inches(2.5), size=18, gap=0.92)
    note = textbox(slide,
                   "The question is not whether an agent can write the change. "
                   "It is what stands between that change and production.",
                   left=MARGIN, top=Inches(5.9), width=Inches(11.0), height=Inches(0.9),
                   size=18, color=CYAN, spacing=1.3)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [note.shape_id])


def slide_solution(prs):
    """OVERVIEW, second half — the pipeline, in the shape the demo will show."""
    slide = new_slide(prs)
    heading(slide, "Nine stages. Three of them are people.", kicker="overview", size=32)
    marks = _spine(slide, top=Inches(2.5))
    legend = textbox(slide,
                     "A filled dot is an agent stage. A ring is a gate — the pipeline stops "
                     "there until a named reviewer approves it in GitHub.",
                     left=MARGIN, top=Inches(3.35), width=Inches(11.0), height=Inches(0.7),
                     size=15, color=DIM, spacing=1.3)
    cards = _rowcards(slide, [
        ("Five agents",
         "planner, developer, reviewer, security, SRE — each an isolated runtime, "
         "one image, five roles."),
        ("Three human gates",
         "GitHub Environments with required reviewers. A gate pauses a JOB, which "
         "is why the pipeline is cut into seven."),
        ("One rule that is not a model",
         "three scanners and a fixed severity threshold. Same input, same answer, "
         "every time."),
    ], top=Inches(4.25), height=Inches(2.0))
    transition(slide)
    animate(slide, [s.shape_id for s in marks if s.has_text_frame]
            + [legend.shape_id] + [s.shape_id for s in cards if s.has_text_frame])


def slide_gate(prs):
    """OVERVIEW — the intellectual core. Determinism on top of non-determinism."""
    slide = new_slide(prs, band=CYAN)
    heading(slide, "Non-deterministic models. A deterministic gate.",
            kicker="overview", size=30, color=CYAN)
    textbox(slide,
            "Every agent here is a language model, and every one of them can be wrong. "
            "The component that stops a change is not one of them.",
            left=MARGIN, top=Inches(1.95), width=Inches(11.0), height=Inches(0.75),
            size=17, color=DIM, spacing=1.3)
    table(slide, ["", "the reviewer", "the security stage"],
          [["what it is", "a model reading the diff", "three scanners and a fixed rule"],
           ["catches", "intent, logic, plan mismatch", "credentials, CVEs, injectable patterns"],
           ["authority", "ADVISORY — it loops, it cannot stop", "BINDING — it ends the run"],
           ["same input twice", "may differ", "identical, always"],
           ["can be argued with", "yes, it is a prompt", "no model is involved"]],
          top=Inches(2.95), left=MARGIN, height=0.5,
          widths=[Inches(2.5), Inches(4.2), Inches(4.4)], mark=4, size=14)
    note = textbox(slide,
                   "The block is a dependency edge, not a status check: the develop stage "
                   "exits 3 and the next gate declares that it needs it. There is no "
                   "condition to misconfigure and no required check to forget.",
                   left=MARGIN, top=Inches(6.05), width=Inches(11.0), height=Inches(0.9),
                   size=15, color=CYAN, spacing=1.3)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_architecture(prs):
    """ARCHITECTURE — an AWS-style diagram, built by architecture/make_architecture.py.

    AN IMAGE, which deckkit's rule against rasterised charts exists to prevent. The
    exception is deliberate: the official AWS icons exist only as draw.io stencils,
    and without them the slide read as six rows of text chips. Rendered at 3x so a
    projector's rescale stays sharp; the editable source is architecture.drawio.

    A COMPACT HEAD, not heading(): its rule sits at 2.06in, which would leave the
    diagram under five inches tall and its labels near 7pt on a projector.
    """
    slide = new_slide(prs)
    textbox(slide, "ARCHITECTURE", left=Inches(0.8), top=Inches(0.3), width=Inches(4),
            height=Inches(0.3), size=12, color=CYAN, bold=True, spacing=1.0)
    textbox(slide, "What runs where — follow the numbers", left=Inches(0.8),
            top=Inches(0.62), width=Inches(11.7), height=Inches(0.6), size=26,
            color=INK, bold=True, spacing=1.0)
    diagram = ROOT / "architecture" / "architecture.png"
    top, bottom = Inches(1.36), Inches(7.38)
    if diagram.exists():
        from PIL import Image
        with Image.open(diagram) as img:
            ratio = img.width / img.height
        height = bottom - top
        width = int(height * ratio)
        if width > SLIDE_W - Inches(0.6):          # never wider than the slide allows
            width = SLIDE_W - Inches(0.6)
            height = int(width / ratio)
        slide.shapes.add_picture(str(diagram), int((SLIDE_W - width) / 2), top, width, height)
    else:
        # Degrade to a labelled placeholder so the deck still builds without draw.io.
        textbox(slide, "architecture.png missing — run architecture/make_architecture.py",
                left=MARGIN, top=Inches(3.5), width=BODY_W, height=Inches(0.5), size=16,
                color=ROSE)
    transition(slide)


def slide_impact(prs):
    """BUSINESS IMPACT — new in the final brief, and stated without overreach."""
    slide = new_slide(prs)
    heading(slide, "What it costs, and what it buys", kicker="business impact", size=32)
    figs = figure(slide, f"${COST_LOW}–{COST_HIGH}", "model cost per change\nthree measured runs",
                  left=MARGIN, top=Inches(2.2), width=Inches(3.4), color=MINT)
    figs += figure(slide, f"{MERGE_MEDIAN_MIN} min", "median ticket to merge\n8 merges",
                   left=Inches(4.8), top=Inches(2.2), width=Inches(3.4), color=CYAN)
    figs += figure(slide, f"{ESCAPES} of {MERGES}", "merged changes carrying\na credential",
                   left=Inches(8.4), top=Inches(2.2), width=Inches(3.4), color=MINT)
    body = bullets(slide, [
        f"Infrastructure is {INFRA_SHARE}% of nothing beside the model: Lambda, "
        "EventBridge and DynamoDB together came to twelve millionths of a dollar "
        "per change. Any cost work that is not prompt caching is noise.",
        "The value is not the cents. It is that a credential cannot reach the "
        "default branch by being approved quickly — refusing that is the one thing "
        "the pipeline does without a model in the path.",
    ], top=Inches(4.3), size=16, gap=0.95)
    caveat = textbox(slide,
                     "Stated honestly: 8 merges of " + str(PIPELINE_RUNS) + " runs, so the "
                     "median is over the ones that finished. And the zero has a positive "
                     f"control — the same scan finds 3 in unmerged PR #{CONTROL_PR}, so it "
                     "is a measurement and not a broken grep.",
                     left=MARGIN, top=Inches(6.3), width=Inches(11.0), height=Inches(0.8),
                     size=13, color=DIM, spacing=1.25)
    transition(slide)
    animate(slide, [s.shape_id for s in figs] + [s.shape_id for s in body] + [caveat.shape_id])


def slide_differentiation(prs):
    """DIFFERENTIATION — new in the final brief. Their words first."""
    slide = new_slide(prs)
    heading(slide, "Every vendor's AI review is advisory. They say so.",
            kicker="differentiation", size=28)
    table(slide, ["product", "from their own documentation"],
          [["GitHub Copilot review", "“will not block merging changes”"],
           ["Anthropic Code Review", "“always completes with a neutral conclusion so it never blocks”"],
           ["OpenAI Codex", "“don't replace tests, branch protections, or required approvals”"],
           ["Cursor Bugbot", "findings “default to neutral” — requiring the status does not block"],
           ["Snyk", "“The generator cannot be the validator.”"]],
          top=Inches(2.25), left=MARGIN, height=0.48,
          widths=[Inches(3.3), Inches(7.8)], mark=4, size=13)
    note = textbox(slide,
                   "So the distinction is not that we are deterministic and they are not — "
                   "Claude Code's permission rules are enforced by the harness rather than "
                   "the model, and Factory blocks a commit outright. The distinction is the "
                   "SEAM: every gate they ship guards a tool call inside one agent's "
                   "session. Ours guards a pipeline stage between agents, with a named "
                   "human reviewer, and the block is a dependency edge.",
                   left=MARGIN, top=Inches(5.3), width=Inches(11.0), height=Inches(1.5),
                   size=15, color=CYAN, spacing=1.3)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_failopen(prs):
    """DIFFERENTIATION, second beat — their failure mode is our design in reverse."""
    slide = new_slide(prs, band=ROSE)
    heading(slide, "Three shipped products fail open", kicker="differentiation",
            size=32, color=ROSE)
    cards = _rowcards(slide, [
        ("Cursor hooks",
         "exit 2 denies. “Other exit codes — hook failed, action proceeds "
         "(fail-open by default).”"),
        ("Claude Code hooks",
         "exit 2 blocks and cannot be overridden. Exit 1 does not block, and "
         "“a mistyped path silently disables the gate”."),
        ("Semgrep",
         "on an internal crash it “sends an anonymous crash report… and returns "
         "exit code 0”."),
    ], top=Inches(2.4), height=Inches(2.1), size=13)
    note = textbox(slide,
                   "A check that did not run, reading as a check that passed. That is the "
                   "single defect shape this project is built to refuse — which is why a "
                   "missing scanner raises here rather than returning an empty list, and "
                   "why an empty list of findings can never be produced by a failure.",
                   left=MARGIN, top=Inches(5.1), width=Inches(11.0), height=Inches(1.2),
                   size=16, color=INK, spacing=1.35)
    transition(slide, kind="fade")
    animate(slide, [s.shape_id for s in cards if s.has_text_frame] + [note.shape_id])


def slide_progress(prs):
    """PROGRESS — what exists, measured today."""
    slide = new_slide(prs)
    heading(slide, "What is built", kicker="progress", size=32)
    figs = figure(slide, f"{PY_TESTS}", f"automated tests\nacross {PY_FILES} files",
                  left=MARGIN, top=Inches(2.1), width=Inches(3.4), color=MINT)
    figs += figure(slide, f"{WEB_TESTS}", f"more for the web app\nacross {WEB_FILES} files",
                   left=Inches(4.8), top=Inches(2.1), width=Inches(3.4), color=MINT)
    figs += figure(slide, f"v{RUNTIME_VERSION}", "five agent runtimes\nall READY, one version",
                   left=Inches(8.4), top=Inches(2.1), width=Inches(3.4), color=CYAN)
    cards = _rowcards(slide, [
        ("Running in the cloud",
         "An issue triggers a Lambda, an event bus dispatches the pipeline, five "
         "runtimes answer, three gates pause for a person."),
        ("A product, not a script",
         "Sign in with GitHub, pick a repository, start a run, watch the stages "
         "move, approve a gate, read the cost."),
        ("Multi-tenant",
         "One DynamoDB table, isolation enforced by the credential rather than by "
         "application code — AWS refuses another tenant's partition."),
    ], top=Inches(4.15), height=Inches(2.05))
    transition(slide)
    animate(slide, [s.shape_id for s in figs] + [s.shape_id for s in cards if s.has_text_frame])


def slide_notes(prs):
    """PROGRESS — the pre-final feedback, answered. The strongest slide here."""
    slide = new_slide(prs)
    heading(slide, "Your ten notes from the pre-final", kicker="progress", size=30)
    table(slide, ["what you asked for", "what exists now"],
          [["Evaluation criteria", "measured arms — a reviewer's miss rate moved 6/8 → 8/8"],
           ["Time and cost vs a coding agent", f"${COST_LOW}–{COST_HIGH} per change, priced from the AWS Pricing API"],
           ["External dependency", f"{VENDOR_MODULES} of {TOTAL_MODULES} modules import a vendor at module level"],
           ["Self-hosted", "one compose file: database, API and web, verified end to end"],
           ["Competitive advantage", "commissioned research; five of our own claims disproved"],
           ["Scanner scoring → go / no-go", "one policy table for three scanners — BUILT BECAUSE OF THIS NOTE"],
           ["Generated tests + Selenium", "tests generated per run; Selenium now runs in CI"],
           ["RAG / knowledge lake", "three curated corpora, wired into four agent prompts"],
           ["A real UI", "sign-in, live run view, gate approval, cost — finished this week"],
           ["Restructure as SaaS", "tenancy, control-plane API, per-tenant isolation"]],
          top=Inches(1.95), left=MARGIN, height=0.42,
          widths=[Inches(4.0), Inches(7.1)], mark=5, size=12)
    transition(slide)


def slide_roadmap(prs):
    """FUTURE WORK — and the gap is named here rather than waited for."""
    slide = new_slide(prs, band=MINT)
    heading(slide, "What is next", kicker="future work", size=32, color=MINT)
    y = Inches(2.3)
    heads = []
    for index, (title, detail, tag) in enumerate([
        ("Apply the change, not just carry it",
         "A merged pull request currently carries the reviewed diff as an artifact. "
         "Applying it to the source is the next step, and it is what would let a "
         "generated test run against the change.", "NEXT"),
        ("Join the two test layers",
         "Tests are generated from the ticket each run; Selenium runs in CI against "
         "the app. Neither verifies the other yet.", "NEXT"),
        ("Prompt caching",
         "Cache hit rate is a measured zero — five agents re-send the same repository "
         "snapshot at four times the cached rate. The only cost work worth doing.", None),
        ("More languages, more scanners",
         "Three scanners and one Python target today. The gate is a table; adding a "
         "scanner is a row.", None),
    ], start=1):
        heads.append(textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.7),
                             height=Inches(0.4), size=15, color=MINT, bold=True, font=MONO))
        label = title if not tag else f"{title}   [{tag}]"
        heads.append(textbox(slide, label, left=Inches(1.9), top=y, width=Inches(4.3),
                             height=Inches(0.7), size=16, color=INK, bold=True, spacing=1.15))
        textbox(slide, detail, left=Inches(6.4), top=y, width=Inches(5.8),
                height=Inches(1.0), size=13, color=DIM, spacing=1.3)
        y += Inches(1.12)
    transition(slide, kind="fade")
    animate(slide, [s.shape_id for s in heads])


def slide_demo(prs):
    """The handover. A holding slide, so the screen is not a dead deck."""
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "The demonstration", left=MARGIN, top=Inches(2.0), width=BODY_W,
            size=44, color=INK, bold=True)
    rule(slide, top=Inches(3.1), width=Inches(2.2), color=CYAN)
    marks = _spine(slide, top=Inches(3.7), stopped_after=4)
    textbox(slide,
            "A ticket that deliberately carries a credential. The scanners find it, "
            "the run stops at the security stage, and nothing after it runs.",
            left=MARGIN, top=Inches(4.6), width=Inches(11.0), height=Inches(0.8),
            size=17, color=DIM, spacing=1.3)
    textbox(slide,
            f"Watch the line numbers: real scanners report {REAL_LINES} and the stand-in "
            f"fixture reports {FIXTURE_LINES}. That pair is the only field that tells the "
            "two apart.",
            left=MARGIN, top=Inches(5.6), width=Inches(11.0), height=Inches(0.8),
            size=15, color=CYAN, spacing=1.3)
    transition(slide, kind="fade")
    void = [s.shape_id for s in marks if s.has_text_frame]
    animate(slide, void)


def slide_team(prs):
    """THE SPEAKER PAGE — second slide, before the agenda. Who is presenting, what
    each person does, and where. Kept to a name, a title and a workplace: the
    repository's rule is "why listen to this person on this subject", not a CV."""
    slide = new_slide(prs)
    heading(slide, "RosettaTeam", kicker="the team · TD63", size=32)
    photo_dir = ROOT / "pitch" / "photos" / "square"
    gap = Inches(0.3)
    width = (BODY_W - gap * (len(TEAM) - 1)) / len(TEAM)
    diameter = Inches(1.45)
    x = MARGIN
    shapes = []
    for filename, name, title, workplace, extra in TEAM:
        photo = photo_dir / filename
        cx = x + width / 2 - diameter / 2
        if photo.exists():
            portrait = slide.shapes.add_picture(str(photo), cx, Inches(2.35), diameter, diameter)
            # PRE-CROPPED SQUARE ON DISK. PowerPoint has no `object-fit: cover` and
            # stretches a non-square image in a square frame.
            portrait.auto_shape_type = MSO_SHAPE.OVAL
        else:
            portrait = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx, Inches(2.35), diameter, diameter)
            portrait.fill.solid()
            portrait.fill.fore_color.rgb = RAISED
            portrait.line.color.rgb = CYAN
        shapes.append(portrait)
        shapes.append(textbox(slide, name, left=x, top=Inches(3.95), width=width,
                              height=Inches(0.4), size=15, color=INK, bold=True,
                              align=PP_ALIGN.CENTER, spacing=1.0))
        shapes.append(textbox(slide, title, left=x, top=Inches(4.38), width=width,
                              height=Inches(0.6), size=13, color=DIM,
                              align=PP_ALIGN.CENTER, spacing=1.1))
        shapes.append(textbox(slide, workplace, left=x, top=Inches(5.02), width=width,
                              height=Inches(0.3), size=11, color=CYAN, bold=True,
                              font=MONO, align=PP_ALIGN.CENTER, spacing=1.0))
        if extra:
            shapes.append(textbox(slide, extra, left=x, top=Inches(5.38), width=width,
                                  height=Inches(0.8), size=11, color=DIM,
                                  align=PP_ALIGN.CENTER, spacing=1.15))
        x += width + gap
    note = textbox(slide,
                   "The work is divided by file rather than by feature, which is how "
                   "fourteen parallel workstreams landed without collisions.",
                   left=MARGIN, top=Inches(6.4), width=Inches(11.0), height=Inches(0.6),
                   size=15, color=DIM, spacing=1.3)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_agenda(prs):
    """THE AGENDA — third slide, so the room stops tracking whether a topic is coming.
    Each row names a section of the brief, what it covers, and its minutes."""
    slide = new_slide(prs)
    heading(slide, "Twenty minutes, in this order", kicker="agenda", size=32)
    y = Inches(2.3)
    for index, (section, detail, minutes) in enumerate(AGENDA, start=1):
        live = section in ("Live demonstration", "Questions")
        textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.6),
                height=Inches(0.36), size=14, color=CYAN, bold=True, font=MONO)
        textbox(slide, section, left=Inches(1.8), top=y, width=Inches(3.0),
                height=Inches(0.36), size=16, color=CYAN if live else INK, bold=True,
                spacing=1.0)
        textbox(slide, detail, left=Inches(4.9), top=y + Inches(0.02), width=Inches(6.0),
                height=Inches(0.36), size=14, color=DIM, spacing=1.0)
        textbox(slide, f"{minutes} min", left=Inches(11.0), top=y + Inches(0.02),
                width=Inches(1.2), height=Inches(0.36), size=13, color=DIM, font=MONO,
                align=PP_ALIGN.RIGHT, spacing=1.0)
        y += Inches(0.54)
    transition(slide)


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
    """OVERVIEW — the scoring, right after the gate it explains. Was a backup slide
    after the close; the judges asked for it by name in the pre-final notes."""
    slide = new_slide(prs)
    heading(slide, "How a finding becomes a verdict", kicker="overview · scoring", size=30)
    table(slide, ["scanner", "how its severity is decided"],
          [["Semgrep", "MAPPED from its own — seven keys across two vocabularies"],
           ["Trivy", "MAPPED from its own; UNKNOWN is a real answer, not a fall-through"],
           ["gitleaks", "ASSIGNED critical by policy — it reports no severity at all"]],
          top=Inches(2.0), left=MARGIN, height=0.5,
          widths=[Inches(2.6), Inches(8.5)], mark=2, size=14)
    body = bullets(slide, [
        "The rule is a comparison: block when any finding sits at or above the "
        "threshold. No model, no network, no ordering dependence.",
        "An unrecognised severity fails closed AT the block threshold, and that "
        "constant is refused at import if it ever drops below it.",
        "The floor is derived from the policy rather than written down twice — two "
        "copies of one fact agree until one of them moves.",
        "A threshold outside the vocabulary is REFUSED, never clamped: clamping "
        "runs the gate at a setting nobody asked for and reports success.",
    ], top=Inches(4.1), size=15, gap=0.72)
    transition(slide)
    animate(slide, [s.shape_id for s in body])


def slide_limits(prs):
    """PROGRESS — the limits, BEFORE the roadmap. Was a backup slide; the repository's
    rule is limitations before the recommendation, not after it."""
    slide = new_slide(prs)
    heading(slide, "What this does not do", kicker="progress · limits", size=30)
    body = bullets(slide, [
        "A repository admin can bypass a gate. It is an operator setting, it is "
        "reported by the pre-flight check on every run, and it is not hidden.",
        "If the scanners miss something, the reviewer is the only thing that saw "
        "it — and the reviewer is advisory. Three human gates are the last line.",
        "One language, one target repository, three scanners. Breadth is where "
        "every competitor is ahead.",
        "A merged pull request carries the reviewed diff as an artifact; applying "
        "it to the source is the next step on the roadmap.",
    ], top=Inches(2.2), size=16, gap=0.95)
    transition(slide)
    animate(slide, [s.shape_id for s in body])


SLIDES = [
    slide_title, slide_team, slide_agenda,
    slide_problem, slide_solution, slide_gate, slide_scoring,
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


def _opening(path, slides, text) -> list[str]:
    """EVERY DECK OPENS WITH A SPEAKER PAGE AND AN AGENDA. See the repository's
    CLAUDE.md, which recommended both for months while this deck had neither: a
    recommendation is fixed per instance, a check is fixed once.

    The agenda must also NAME every required section, and its minutes must fill
    the slot -- an agenda that omits a section, or promises 23 minutes of a 20-minute
    slot, is worse than none because the room believes it.
    """
    from pptx import Presentation as _Presentation
    names = [fn.__name__ for fn in slides]
    problems = []
    if "slide_team" not in names or "slide_agenda" not in names:
        return ["no speaker page or no agenda: every deck opens with both"]
    if names[0] != "slide_title" or set(names[1:3]) != {"slide_team", "slide_agenda"}:
        problems.append(f"slides 2 and 3 must be the speaker page and the agenda; "
                        f"they are {names[1:3]}")
    agenda = " ".join(shape.text_frame.text for shape in
                      _Presentation(path).slides[names.index("slide_agenda")].shapes
                      if shape.has_text_frame).upper()
    missing = [section for section in _REQUIRED if section not in agenda]
    if missing:
        problems.append(f"the agenda does not name: {', '.join(missing)}")
    total = OPENING_MINUTES + sum(minutes for _, _, minutes in AGENDA)
    if total != SLOT_MINUTES:
        problems.append(f"the agenda's minutes sum to {total}, the slot is {SLOT_MINUTES}")
    return problems


def main() -> int:
    out = build(SLIDES, ROOT / "pitch" / "TheAgentOrg-Final.pptx")
    code = verify(out, SLIDES, required=_REQUIRED, banned=_BANNED, static=_STATIC,
                  extra=[_exposition_order, _opening])
    kind = subprocess.run(["file", "-b", str(out)], capture_output=True, text=True,
                          check=False).stdout.strip()
    print(f"  file(1):     {kind}")
    return code


if __name__ == "__main__":
    sys.exit(main())
