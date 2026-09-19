#!/usr/bin/env python3
"""Build the RosettaCloud pitch deck for the GenAI for Education Hackathon 2026.

    .venv-deck/bin/python talks/rosettacloud-genai-hackathon/build_deck.py

Content only -- the engine is deckkit/deck.py. This deck answers the hackathon's
Startup Track upload spec exactly: problem, target market, current solution,
traction, business model, GenAI integration, competitive differentiation, team,
growth/impact evidence.

REGISTER. This is a pitch deck, not a technical talk, but the same discipline
applies: every figure here is one already used and defended in the project's own
verified article claims and pilot-testing notes -- nothing invented for this deck.
Where a number is a plan rather than a measurement (planned pricing, a roadmap
step), the slide says so with a PLANNED tag rather than presenting it as fact.

THIS IS AN AI COMPETITION -- LEAD WITH THE TUTOR, NOT THE CLUSTER. An earlier
draft opened on "real infrastructure" and treated the three-agent tutor as one
section among nine. For a GenAI audience that inverts the actual pitch: the
infrastructure is what makes the tutoring genuine (the grader reads a real exit
code, not a self-report) rather than the headline attraction on its own. Every
slide below leads with the AI-tutoring claim and uses the infrastructure as its
evidence, not the other way around.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from deckkit import deck
from deckkit.deck import *  # noqa: F403 -- palette, geometry, primitives, build, verify

ROOT = pathlib.Path(__file__).resolve().parent
deck.VIDEO_DIR = ROOT / "pitch" / "video"  # unused here; no recorded demos in a pitch deck

# ── palette -- RosettaCloud's own brand, not the conference-talk deck's ────────
# SLATE is shifted to the exact basalt hex RosettaCloud already uses on its OG
# card and logo (#171D1B). CYAN/MINT/ROSE are deckkit's own validated values --
# CYAN vs DIM measures dE 12.1 (deutan) on this surface; reinventing the accent
# without redoing that check would be a downgrade, not customization. An
# earlier draft of this deck used a gold accent instead; dropped on request.
# SET THROUGH deck.palette(), NOT BY REASSIGNING THE IMPORTED NAMES. `import *` copies
# values; rebinding them here would leave the engine's own defaults in place, so this
# deck came out with brand colours only where a colour was passed explicitly and engine
# colours everywhere else. palette() sets them on the engine itself.
deck.palette(
    VOID=RGBColor(0x0A, 0x0C, 0x10),
    SLATE=RGBColor(0x17, 0x1D, 0x1B),
    RAISED=RGBColor(0x1F, 0x26, 0x23),
    LINE=RGBColor(0x2B, 0x32, 0x2E),
    INK=RGBColor(0xF1, 0xEC, 0xDD),
    DIM=RGBColor(0x94, 0xA0, 0x99),
)
VOID, SLATE, RAISED = deck.VOID, deck.SLATE, deck.RAISED
LINE, INK, DIM = deck.LINE, deck.INK, deck.DIM
CYAN, MINT, ROSE = deck.CYAN, deck.MINT, deck.ROSE

# ── figures, each traceable to the project's own verified claims / pilot notes ─
LAB_READY_SECS = "<10s"
AWS_SERVICES = 17
CICD_PIPELINES = 11

FREE_COST_MO = 0.40         # fully-loaded: spot compute + Nova 2 Lite inference
PAID_PRICE_MO = 20          # mid-point of the planned $15-25/mo individual tier
GROSS_MARGIN_PCT = 98
FREE_USERS_PER_PAID = 46

SKILL_BUILDER_PRICE = 29
COURSERA_PRICE = 24
KODEKLOUD_AI_PRICE = 46
ROSETTACLOUD_PRICE = 15     # low end of the planned range, shown conservatively

_REQUIRED = (
    "PROBLEM", "TARGET MARKET", "CURRENT SOLUTION", "TRACTION",
    "BUSINESS MODEL", "GENAI INTEGRATION", "COMPETITIVE DIFFERENTIATION",
    "TEAM", "GROWTH",
)

# Anthropomorphism/dramatization bans, ported from the conference-talk deck's
# register rules -- they apply just as much to describing an AI tutor's
# behaviour in a pitch deck as to a technical report. A second group bans the
# stock superlatives a pitch deck reaches for by reflex.
_BANNED = (
    r"\bit lied\b", r"\bknows\b", r"\bwants to\b", r"\btried to\b", r"\bunderstands\b",
    r"\brevolutionary\b", r"\bgame.?chang", r"\bcutting.?edge\b", r"\bdisrupt",
    r"\bworld.?class\b", r"\bsynerg",
)


def _card_row(slide, items, *, top, height=Inches(2.15), gap=Inches(0.28)):
    """A row of equal-width raised cards. `items` is [(title, body), ...]."""
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
        # BODY OFFSET LEAVES ROOM FOR A TWO-LINE TITLE, not just the one-line case --
        # a title that wraps to a second line at this width previously collided with
        # the body starting at a fixed 0.72in offset. 0.98in clears two lines at 17pt.
        shapes.append(textbox(slide, title, left=x + Inches(0.22), top=top + Inches(0.2),
                             width=width - Inches(0.4), height=Inches(0.78),
                             size=17, color=CYAN, bold=True, spacing=1.1))
        shapes.append(textbox(slide, body, left=x + Inches(0.22), top=top + Inches(0.98),
                             width=width - Inches(0.4), height=height - Inches(1.16),
                             size=13, color=DIM, spacing=1.3))
        x += width + gap
    return shapes


# ── slides ────────────────────────────────────────────────────────────────────

def slide_title(prs):
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "AN AI TUTOR THAT\nWON'T JUST ANSWER", left=MARGIN, top=Inches(1.7),
          width=BODY_W, height=Inches(1.7), size=52, color=INK, bold=True, spacing=1.03)
    rule(slide, top=Inches(3.55), width=Inches(2.6), color=CYAN)
    textbox(slide, "A hint-first, multi-agent tutor for software and cloud engineering—"
                 "grounded in a real, working environment, not a chat window.",
          left=MARGIN, top=Inches(3.95), width=Inches(10.6), size=21, color=DIM, spacing=1.3)
    textbox(slide, "ROSETTACLOUD", left=MARGIN, top=Inches(5.7), width=Inches(6),
          height=Inches(0.4), size=12, color=CYAN, bold=True, font=MONO, spacing=1.0)
    textbox(slide,
        "GenAI for Education Hackathon 2026 · Startup Track · Category: AI Tutor\n"
        "Mohamed Sorour · Mohamed Talal · Moaz Gamal",
          left=MARGIN, top=Inches(6.15), width=BODY_W, size=14, color=DIM, spacing=1.4)
    transition(slide, kind="fade")


def slide_problem(prs):
    """01 -- the problem is framed as a tutoring failure, not an access failure."""
    slide = new_slide(prs)
    heading(slide, "Chatbots answer. That's the problem.", kicker="problem", size=34)
    body = bullets(slide, [
        "Generic AI assistants and coding copilots hand over the answer on "
        "request — a student learns to accept a suggestion, not to reason "
        "through a problem.",
        "Hands-on platforms bolt AI on afterward: it validates what a student "
        "already built, or answers a question like any chatbot — it doesn't "
        "shape how they got there.",
        "Nobody pairs a tutor built to withhold the answer with an environment "
        "real enough for that restraint to matter.",
    ], top=Inches(2.75), size=18, gap=0.95)
    note = textbox(slide,
        "That's the gap RosettaCloud fills: a tutor engineered to guide instead "
        "of answer, working inside real infrastructure instead of a sandboxed chat.",
        left=MARGIN, top=Inches(6.15), width=Inches(11.0), height=Inches(0.85),
        size=17, color=CYAN)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [note.shape_id])


def slide_market(prs):
    """02 -- who it's for, with the AI-specific "why now"."""
    slide = new_slide(prs)
    heading(slide, "Hired, not certified.", kicker="target market", size=32)
    cards = _card_row(slide, [
        ("Primary — students",
         "Early-career engineers in developing economies who need a tutor "
         "and a real lab they can actually afford. First validated in Egypt."),
        ("Secondary — institutions",
         "Bootcamps and universities that need AI-tutored labs for a cohort "
         "without building and running them. Bulk licensing, one decision."),
        ("Why now",
         "Coding copilots teach students to accept suggestions, not "
         "understand them. The same GenAI wave makes a hint-first tutor "
         "possible at this cost."),
    ], top=Inches(2.85), height=Inches(2.6))
    transition(slide)
    animate(slide, [s.shape_id for s in cards if s.has_text_frame])


def slide_solution(prs):
    """03 -- lead with the tutor, infrastructure as the evidence behind it."""
    slide = new_slide(prs)
    heading(slide, "A tutor that guides, for real.", kicker="current solution", size=32)
    body = bullets(slide, [
        "A three-agent AI system — tutor, grader, planner — gives hints "
        "grounded in the real curriculum, never the answer outright.",
        "Grading isn't self-reported: the grader checks a student's actual "
        "submitted work by exit code, inside their own environment.",
        "That environment is real — a dedicated Kubernetes cluster and Docker "
        "daemon per student — so the tutor is coaching genuine practice.",
    ], top=Inches(2.6), size=16, gap=0.68)
    figs = figure(slide, LAB_READY_SECS, "from “Start Lab”\nto a running pod",
                  left=MARGIN, top=Inches(5.65), width=Inches(3.2))
    figs += figure(slide, str(AWS_SERVICES), "AWS services across\nthe platform",
                    left=Inches(4.7), top=Inches(5.65), color=CYAN, width=Inches(3.2))
    figs += figure(slide, str(CICD_PIPELINES), "automated CI/CD\npipelines",
                    left=Inches(8.4), top=Inches(5.65), width=Inches(3.2))
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [s.shape_id for s in figs])


def slide_solution_status(prs):
    """03b -- the honest status note gets its own quiet beat, not a footnote."""
    slide = new_slide(prs)
    heading(slide, "Where it stands today", kicker="current solution", size=32)
    note = textbox(slide,
        "The platform was substantially rebuilt this year — migrating off an "
        "earlier Python monolith onto hardened Java microservices — and every "
        "service is proven deployable end to end by CI on every change.",
        left=MARGIN, top=Inches(2.7), width=Inches(11.0), height=Inches(1.3),
        size=20, color=INK, spacing=1.4)
    note2 = textbox(slide,
        "It is not continuously serving public traffic at this moment. "
        "Redeploying to a persistent environment is the immediate next step, "
        "not an open engineering question.",
        left=MARGIN, top=Inches(4.3), width=Inches(11.0), height=Inches(1.1),
        size=18, color=DIM, spacing=1.4)
    transition(slide, kind="fade")
    animate(slide, [note.shape_id, note2.shape_id])


def slide_traction(prs):
    """04 -- validated early, honestly framed as three testers, not a cohort."""
    slide = new_slide(prs)
    heading(slide, "Validated by the people it's for.", kicker="traction", size=30)
    cards = _card_row(slide, [
        ("Nehal Hassan — DevOps",
         "lab 5/5 · AI 5/5\n“More useful than KodeKloud.”\nWould pay $10–15/mo"),
        ("Mohamed Talal — AI Eng.",
         "lab 5/5 · AI 4/5\nFound a real history bug.\nWould pay $25+/mo"),
        ("Moaz Gamal — AI Eng.",
         "lab 5/5 · AI 5/5\n“More agentic — not just Q&A.”\nWould pay $15–25/mo"),
    ], top=Inches(2.75), height=Inches(2.15))
    note = textbox(slide,
        "AWS AIdeas 2025 — Top-50 Finalist, Social Impact category, selected "
        "from thousands of global submissions. Judges' feedback highlighted: "
        "production-grade technical execution · hint-first pedagogy well "
        "implemented · real infrastructure rather than simulation.",
        left=MARGIN, top=Inches(5.15), width=Inches(11.0), height=Inches(1.05),
        size=15, color=CYAN, spacing=1.3)
    caveat = textbox(slide,
        "Early-stage: three testers, not yet a cohort. Next milestone is a "
        "structured pilot with a full class.",
        left=MARGIN, top=Inches(6.45), width=Inches(11.0), height=Inches(0.45),
        size=13, color=DIM)
    transition(slide)
    animate(slide, [s.shape_id for s in cards if s.has_text_frame] + [note.shape_id, caveat.shape_id])


def slide_business(prs):
    """05 -- freemium funded by a deliberately cheap tutor, not venture burn."""
    slide = new_slide(prs)
    heading(slide, "Freemium economics: forty cents a month.", kicker="business model", size=28)
    table(slide, ["tier", "who", "allowance", "price"],
          [["Free", "Any student", "2h lab + 50 AI msgs / week", "$0"],
           ["Individual", "Committed learners", "Unlimited labs, full tutor",
            f"${PAID_PRICE_MO-5}–{PAID_PRICE_MO+5}/mo  (planned)"],
           ["University / bootcamp", "Institutions, per cohort", "Bulk seats, admin dashboard",
            "$8–12/student/mo  (planned)"]],
          top=Inches(2.7), left=MARGIN,
          widths=[Inches(2.3), Inches(2.6), Inches(3.7), Inches(2.5)], mark=1, size=15)
    note = textbox(slide,
        "Funded by spot-instance compute and a deliberately cheap inference "
        "model — not by venture-scale burn.",
        left=MARGIN, top=Inches(5.3), width=Inches(10.5), height=Inches(0.6),
        size=17, color=DIM)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_business_economics(prs):
    """05b -- the ratio and the margin get their own slide, room to read clearly."""
    slide = new_slide(prs)
    heading(slide, "The ratio behind a sustainable free tier.", kicker="business model", size=28)
    drawn = bars(slide, [
        ("Cost to serve one free user", 40, DIM, f"${FREE_COST_MO:.2f}"),
        ("Individual plan price (mid-point)", int(PAID_PRICE_MO * 100), MINT, f"${PAID_PRICE_MO}"),
    ], left=MARGIN, top=Inches(2.75), width=Inches(9.3), height=Inches(1.2))
    figs = figure(slide, f"~{GROSS_MARGIN_PCT}%", "gross margin on\nthe individual plan",
                  left=MARGIN, top=Inches(5.05), width=Inches(3.5), color=MINT)
    figs += figure(slide, f"1:{FREE_USERS_PER_PAID}", "one paid user funds\nthis many free ones",
                    left=Inches(4.9), top=Inches(5.05), width=Inches(3.5), color=CYAN)
    figs += figure(slide, f"${FREE_COST_MO:.2f}", "fully-loaded monthly\ncost per free user",
                    left=Inches(8.6), top=Inches(5.05), width=Inches(3.5))
    transition(slide)
    animate(slide, [s.shape_id for s in drawn] + [s.shape_id for s in figs])


def slide_genai(prs):
    """06 -- the architecture is the centrepiece of the deck, not a footnote."""
    slide = new_slide(prs)
    heading(slide, "Three agents. Hint-first, by design.", kicker="genai integration", size=30)
    layers = [
        ("TUTOR", "retrieves the real curriculum (Titan embeddings, LanceDB) and "
                  "hints toward it — calibrated to withhold the direct answer"),
        ("GRADER", "reads the exit code from a student's real submitted work "
                   "inside their own lab — not a self-report"),
        ("PLANNER", "sequences the next step from a student's actual progress, "
                    "with memory that persists across sessions"),
    ]
    cards = []
    y = Inches(2.65)
    for name, detail in layers:
        card = slide.shapes.add_shape(1, MARGIN, y, Inches(11.0), Inches(0.9))
        card.fill.solid(); card.fill.fore_color.rgb = RAISED
        card.line.color.rgb = CYAN; card.line.width = Pt(1.25)
        card.shadow.inherit = False
        cards.append(card)
        textbox(slide, name, left=MARGIN + Inches(0.3), top=y + Inches(0.27),
              width=Inches(2.1), height=Inches(0.36), size=13, color=CYAN, font=MONO, bold=True)
        textbox(slide, detail, left=MARGIN + Inches(2.6), top=y + Inches(0.2),
              width=Inches(8.1), height=Inches(0.55), size=14, color=INK, spacing=1.25)
        y += Inches(1.05)
    note = textbox(slide,
        "Built on Amazon Bedrock AgentCore and Amazon Nova — the entire AI "
        "layer is AWS-native; no third-party model sits in the request path.",
        left=MARGIN, top=Inches(6.15), width=Inches(11.0), height=Inches(0.65),
        size=15, color=DIM, spacing=1.3)
    transition(slide)
    animate(slide, [c.shape_id for c in cards] + [note.shape_id])


def slide_genai_why(prs):
    """06b -- the "why GenAI, specifically" the form's own field also asks for."""
    slide = new_slide(prs, band=CYAN)
    heading(slide, "Why this needs GenAI.", kicker="genai integration", size=32, color=CYAN)
    body = bullets(slide, [
        "A fixed curriculum can't respond to what a specific student typed "
        "into their own terminal and got wrong.",
        "A rules engine can't paraphrase the same hint three different ways "
        "when a student is still stuck — that requires reasoning over "
        "open-ended, student-specific state.",
        "Not a Copilot clone: GitHub Copilot and similar tools autocomplete "
        "the answer. This tutor is deliberately built to withhold it — a "
        "pedagogical stance, not a missing feature.",
    ], top=Inches(2.8), size=19, gap=1.05)
    transition(slide)
    animate(slide, [s.shape_id for s in body])


def slide_competitive(prs):
    """07 -- AI tutoring style is the lead column, infra access is the second."""
    slide = new_slide(prs)
    heading(slide, "Everyone else answers. Nobody guides first.", kicker="competitive differentiation", size=27)
    table(slide, ["platform", "ai tutoring style", "hands-on infra", "price / mo"],
          [["AWS Skill Builder", "Answers questions", "Console sandbox, guided", f"${SKILL_BUILDER_PRICE}"],
           ["Coursera Plus", "QA bot over videos", "Browser notebooks", f"~${COURSERA_PRICE}"],
           ["GitHub Copilot / Codespaces", "Autocompletes the answer", "No privileged access", "~$0.18/hr"],
           ["KodeKloud (AI tier)", "Validates after the fact", "Shared, pre-existing sandbox", f"${KODEKLOUD_AI_PRICE}"],
           ["RosettaCloud", "Hint-first, before trying", "Own cluster, per student", f"${ROSETTACLOUD_PRICE}–25"]],
          top=Inches(2.45), left=MARGIN, height=0.46,
          widths=[Inches(2.85), Inches(3.1), Inches(3.0), Inches(2.15)], mark=4, size=13)
    drawn = bars(slide, [
        ("AWS Skill Builder", SKILL_BUILDER_PRICE, DIM, f"${SKILL_BUILDER_PRICE}"),
        ("Coursera Plus", COURSERA_PRICE, DIM, f"${COURSERA_PRICE}"),
        ("KodeKloud (AI tier)", KODEKLOUD_AI_PRICE, DIM, f"${KODEKLOUD_AI_PRICE}"),
        ("RosettaCloud (planned)", ROSETTACLOUD_PRICE, MINT, f"${ROSETTACLOUD_PRICE}"),
    ], left=MARGIN, top=Inches(5.45), width=Inches(9.3), height=Inches(1.75), bar_h=0.3, gap=0.14)
    transition(slide)
    animate(slide, [s.shape_id for s in drawn])


def slide_team(prs):
    """08 -- three engineers, photographed, roles honest about scope."""
    slide = new_slide(prs)
    heading(slide, "Three engineers, one platform.", kicker="team", size=32)
    people = [
        ("sorour-circle.png", "Mohamed Sorour", "Founder & Engineer",
         "Senior DevOps Engineer, AWS Community Builder. Designed and built "
         "the platform end to end — microservices, Kubernetes-based lab "
         "provisioning, CI/CD, and the multi-agent tutor."),
        ("talal-circle.png", "Mohamed Talal", "AI Engineer",
         "Works on the tutoring system's agent design and evaluation. One of "
         "the platform's earliest testers — found a real conversation-history "
         "bug before it reached students."),
        ("moaz-circle.png", "Moaz Gamal", "AI Engineer",
         "Works on the tutoring system's agent design and evaluation. An "
         "early tester whose feedback pushed the tutor from simple Q&A "
         "toward genuinely agentic help."),
    ]
    photo_dir = ROOT / "pitch" / "photos" / "square"
    x = MARGIN
    width = (BODY_W - Inches(0.5) * 2) / 3
    diameter = Inches(1.85)
    photo_top = Inches(2.65)
    shapes = []
    for filename, name, role, bio in people:
        photo = photo_dir / filename
        cx = x + width / 2 - diameter / 2
        # THE CIRCLE IS BAKED INTO THE PNG, not applied as a PowerPoint mask.
        # add_picture + auto_shape_type=OVAL looked correct in the saved XML but
        # rendered off-centre in PowerPoint (photo content pushed toward one
        # corner, consistently, across all three images) -- a real, reproducible
        # rendering bug in that combination, not a crop issue. Pre-rendering the
        # circular crop and ring in PIL sidesteps it: this is a plain rectangular
        # picture whose visible pixels already form the circle, so there is
        # nothing left for PowerPoint's shape geometry to get wrong.
        if photo.exists():
            portrait = slide.shapes.add_picture(str(photo), cx, photo_top, diameter, diameter)
        else:
            portrait = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx, photo_top, diameter, diameter)
            portrait.fill.solid(); portrait.fill.fore_color.rgb = RAISED
            portrait.line.color.rgb = CYAN; portrait.line.width = Pt(2)
            portrait.shadow.inherit = False
        shapes.append(portrait)
        shapes.append(textbox(slide, name, left=x, top=Inches(4.75), width=width,
                             height=Inches(0.4), size=18, color=INK, bold=True,
                             align=PP_ALIGN.CENTER))
        shapes.append(textbox(slide, role.upper(), left=x, top=Inches(5.2), width=width,
                             height=Inches(0.3), size=11, color=CYAN, bold=True,
                             align=PP_ALIGN.CENTER, font=MONO, spacing=1.0))
        shapes.append(textbox(slide, bio, left=x, top=Inches(5.58), width=width,
                             height=Inches(1.4), size=12.5, color=DIM,
                             align=PP_ALIGN.CENTER, spacing=1.3))
        x += width + Inches(0.5)
    transition(slide)
    animate(slide, [s.shape_id for s in shapes if hasattr(s, "shape_id")])


def slide_growth(prs):
    """09 -- external signal before any marketing spend, plan clearly tagged."""
    slide = new_slide(prs, band=MINT)
    heading(slide, "Signal, before a dollar of marketing.", kicker="growth & impact evidence", size=30, color=MINT)
    heads = []
    y = Inches(2.7)
    for index, (title, detail, tag) in enumerate([
        ("3 for 3 on lab quality",
         "Every pilot tester rated the lab 5/5 and stated a willingness to "
         "pay $10–25+/month — before any pricing existed.", None),
        ("AIdeas 2025 — Top-50 Finalist",
         "Selected from thousands of global submissions, Social Impact "
         "category — independent, competitive validation.", None),
        ("Platform rebuilt on hardened infrastructure",
         "Migrated to Java microservices with security-hardened, "
         "CI-verified deployments — ready to serve a real cohort.", None),
        ("Redeploy, then a structured cohort pilot",
         "Bring the platform back to a persistent environment, run a "
         "full-class pilot, then open freemium growth and approach "
         "bootcamps for bulk licensing.", "PLAN"),
    ], start=1):
        heads.append(textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.7),
                            height=Inches(0.4), size=15, color=MINT, bold=True, font=MONO))
        label = title if not tag else f"{title}   [{tag}]"
        heads.append(textbox(slide, label, left=Inches(1.95), top=y, width=Inches(4.5),
                            height=Inches(0.62), size=16.5, color=INK, bold=True, spacing=1.15))
        textbox(slide, detail, left=Inches(6.6), top=y, width=Inches(5.6),
              height=Inches(0.85), size=13.5, color=DIM, spacing=1.3)
        y += Inches(1.02)
    transition(slide, kind="fade")
    animate(slide, [s.shape_id for s in heads])


def slide_close(prs):
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "Thank you", left=MARGIN, top=Inches(2.35), width=BODY_W,
          size=50, color=INK, bold=True)
    rule(slide, top=Inches(3.6), width=Inches(2.2), color=CYAN)
    textbox(slide, "Questions", left=MARGIN, top=Inches(4.1), width=Inches(6.0),
          height=Inches(0.65), size=30, color=CYAN, bold=True)
    textbox(slide,
        "Mohamed Sorour · Mohamed Talal · Moaz Gamal\n"
        "GenAI for Education Hackathon 2026 · Startup Track",
          left=MARGIN, top=Inches(6.2), width=BODY_W, size=15, color=DIM, spacing=1.4)
    transition(slide, kind="fade")


SLIDES = [
    slide_title, slide_problem, slide_market, slide_solution, slide_solution_status,
    slide_traction, slide_business, slide_business_economics, slide_genai, slide_genai_why,
    slide_competitive, slide_team, slide_growth, slide_close,
]
_STATIC = 3


def main() -> int:
    out = build(SLIDES, ROOT / "pitch" / "RosettaCloud-Pitch-Deck.pptx")
    code = verify(out, SLIDES, required=_REQUIRED, banned=_BANNED, static=_STATIC)
    kind = subprocess.run(["file", "-b", str(out)], capture_output=True, text=True,
                          check=False).stdout.strip()
    print(f"  file(1):     {kind}")
    return code


if __name__ == "__main__":
    sys.exit(main())
