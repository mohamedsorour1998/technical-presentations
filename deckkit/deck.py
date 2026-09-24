#!/usr/bin/env python3
"""deckkit — a reusable engine for building technical conference decks as .pptx.

    from deckkit import *                     # palette, geometry, primitives
    from deckkit import build, verify

    SLIDES = [slide_title, slide_agenda, ...] # your talk supplies these
    build(SLIDES, pathlib.Path("out.pptx"))
    verify(out, SLIDES, required=(...), banned=(...))

WHAT LIVES HERE AND WHAT DOES NOT
=================================
This module knows how to draw a slide, a chart and a recorded demonstration, and how to
check the saved file. It knows nothing about any particular talk. Content -- the
constants, the slide functions, the section list -- belongs in a build script beside it.

The split exists so a second talk starts by writing slide functions, not by copying and
diverging a thousand-line generator.

TRANSITIONS AND ANIMATIONS ARE NOT A python-pptx FEATURE
========================================================
Verified before relying on it: `dir(slide)` exposes nothing matching "trans" or "anim".
python-pptx models shapes and text, not the timing tree. Both live in the slide's raw
XML, which it does expose, so `transition` and `animate` write that XML directly and
`verify` reads the saved archive back to count them -- python-pptx cannot report them
missing because it never knew they existed.

A SLIDE'S CHILDREN ARE ORDERED cSld, clrMapOvr, transition, timing
==================================================================
The order is not advisory. Get it wrong and PowerPoint opens the file as "Repaired",
which the audience reads in the title bar. This bites the moment a slide holds video:
`add_movie` builds a timing tree of its own, so a transition appended to the slide lands
after it. `transition` inserts before any existing timing for exactly that reason.
"""

from __future__ import annotations

import itertools
import json
import pathlib
import re
import subprocess
import sys
import zipfile

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

# Where video() looks for <name>.mp4 and <name>.png unless a folder is passed. A build
# script sets this once: deckkit.VIDEO_DIR = ROOT / "pitch" / "video".
VIDEO_DIR = pathlib.Path("video")

__all__ = [
    "VIDEO_DIR",
    # palette
    "VOID", "SLATE", "RAISED", "TERM", "LINE", "INK", "DIM", "CYAN", "ROSE", "MINT",
    "SANS", "MONO",
    # geometry
    "SLIDE_W", "SLIDE_H", "MARGIN", "BODY_W", "RULE_W", "STAT_W",
    # primitives
    "new_slide", "textbox", "rule", "heading", "slide_number", "bullets", "figure",
    "table", "terminal", "video",
    # charts
    "bars", "line_chart", "quadrant",
    # motion
    "transition", "animate",
    # pipeline
    "build", "verify", "palette", "add_notes", "RULE_NAME",
    # re-exported so a build script needs one import
    "Emu", "Inches", "Pt", "RGBColor", "MSO_SHAPE", "PP_ALIGN", "Presentation",
    "pathlib",
]

# ── palette ───────────────────────────────────────────────────────────────────
# Ported verbatim from pitch/preview/index.html.
VOID = RGBColor(0x0A, 0x0C, 0x10)     # deepest surface, section markers
SLATE = RGBColor(0x14, 0x18, 0x1F)    # the standard slide surface
RAISED = RGBColor(0x1C, 0x22, 0x30)   # cards and panels
TERM = RGBColor(0x07, 0x09, 0x0C)     # terminal blocks
LINE = RGBColor(0x2A, 0x32, 0x42)     # hairlines
INK = RGBColor(0xE8, 0xED, 0xF4)      # primary text: off-white, never pure white
DIM = RGBColor(0x8A, 0x94, 0xA6)      # secondary text
CYAN = RGBColor(0x4F, 0xD1, 0xC5)     # structure: kickers, rules, identifiers
ROSE = RGBColor(0xFF, 0x6B, 0x6B)     # measured shortfalls
MINT = RGBColor(0x4A, 0xDE, 0x80)     # measured results
SANS = "Helvetica Neue"
MONO = "Menlo"                        # identifiers and figures


_PALETTE = ("VOID", "SLATE", "RAISED", "TERM", "LINE", "INK", "DIM", "CYAN", "ROSE",
            "MINT", "SANS", "MONO")


def palette(**overrides):
    """Rebrand the engine's palette. Call this before building any slide.

    A TALK CANNOT REBRAND BY REASSIGNING THE NAMES IT IMPORTED. `from deckkit.deck import
    *` copies values into the talk's namespace; rebinding SLATE there leaves the engine's
    own SLATE untouched, and every primitive that falls back to a default keeps using it.
    The first deck to try that came out with brand colours where it passed a colour
    explicitly and engine colours everywhere else -- a mix nobody would choose, and one
    that looks deliberate enough to survive a read-through.

    So overrides are set here, on the engine's own module, and every primitive resolves
    its palette default at call time rather than at import.

        deck.palette(SLATE=RGBColor(0x17, 0x1D, 0x1B),
                     INK=RGBColor(0xF1, 0xEC, 0xDD))

    Re-run the contrast and CVD validator after changing a surface or an accent. The
    published figures in CLAUDE.md were measured against the default SLATE and do not
    carry over to a new one.
    """
    unknown = set(overrides) - set(_PALETTE)
    if unknown:
        raise ValueError(f"not palette names: {', '.join(sorted(unknown))}. "
                         f"Known: {', '.join(_PALETTE)}")
    globals().update(overrides)


P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)

# Hoisted to module scope: ruff B008 forbids a call in an argument default.
MARGIN = Inches(1.1)
RULE_NAME = "deckkit-rule"
BODY_W = Inches(11.1)
RULE_W = Inches(1.6)
STAT_W = Inches(3.4)


def transition(slide, *, kind: str = "wipe", direction: str = "l") -> None:
    """Attach an entrance transition to this slide.

    Appended to <p:sld> as its LAST child, which the schema requires. An element out of
    order makes PowerPoint declare the file corrupt and offer to repair it, which on a
    projector is indistinguishable from a broken deck.
    """
    element = etree.Element(P_NS + "transition")
    element.set("spd", "med")
    child = etree.SubElement(element, P_NS + kind)
    if kind in ("wipe", "push", "pull", "cover"):
        child.set("dir", direction)

    # INSERTED BEFORE <p:timing>, NOT APPENDED. The schema orders a slide's children
    # cSld, clrMapOvr, transition, timing -- and `add_movie` creates a timing tree of its
    # own so the video can play. Appending the transition after that put the two in the
    # wrong order on every video slide, and PowerPoint opened the file as "Repaired".
    timing = slide._element.find(P_NS + "timing")
    if timing is not None:
        timing.addprevious(element)
    else:
        slide._element.append(element)


def animate(slide, shape_ids: list[int]) -> None:
    """Reveal these shapes one click at a time, in the order given.

    A single <p:timing> tree holding click-triggered fades. Written as a string rather
    than assembled element by element: the nesting is five levels deep, and the shape of
    the output is far easier to read and correct this way.

    Each shape needs <p:set> to become visible AND <p:animEffect filter="fade">. Without
    the <p:set> the shape is on screen from the start and the fade animates something
    already visible.
    """
    if not shape_ids:
        return

    node = 10
    blocks = []
    for index, shape_id in enumerate(shape_ids):
        blocks.append(f"""
        <p:par><p:cTn id="{node}" fill="hold">
          <p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>
          <p:childTnLst><p:par><p:cTn id="{node + 1}" fill="hold">
            <p:stCondLst><p:cond delay="0"/></p:stCondLst>
            <p:childTnLst><p:par><p:cTn id="{node + 2}" presetID="10"
                presetClass="entr" presetSubtype="0" fill="hold"
                grpId="0" nodeType="{"clickEffect" if index == 0 else "afterEffect"}">
              <p:stCondLst><p:cond delay="0"/></p:stCondLst>
              <p:childTnLst>
                <p:set><p:cBhvr><p:cTn id="{node + 3}" dur="1" fill="hold"/>
                  <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                  <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                </p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
                <p:animEffect transition="in" filter="fade">
                  <p:cBhvr><p:cTn id="{node + 4}" dur="450"/>
                    <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl></p:cBhvr>
                </p:animEffect>
              </p:childTnLst></p:cTn></p:par></p:childTnLst>
          </p:cTn></p:par></p:childTnLst>
        </p:cTn></p:par>""")
        node += 10

    timing = f"""<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
      <p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
        <p:childTnLst><p:seq concurrent="1" nextAc="seek">
          <p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
            {"".join(blocks)}
          </p:childTnLst></p:cTn>
          <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
          <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
        </p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>"""
    slide._element.append(etree.fromstring(timing))


def new_slide(prs, *, band=None, surface=None):
    """A slide with no placeholders.

    Layout 6 is the blank one. The placeholder layouts fight explicit positioning: a
    title placeholder re-centres itself and cannot be moved reliably across PowerPoint
    and Keynote, so every text box in this deck is built by hand.

    `band` paints a colour block down the left edge -- the deck's one recurring ornament.
    """
    surface = SLATE if surface is None else surface
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.shapes.add_shape(1, 0, 0, SLIDE_W, SLIDE_H)
    background.fill.solid()
    background.fill.fore_color.rgb = surface
    background.line.fill.background()
    background.shadow.inherit = False
    if band is not None:
        strip = slide.shapes.add_shape(1, 0, 0, Inches(0.34), SLIDE_H)
        strip.fill.solid()
        strip.fill.fore_color.rgb = band
        strip.line.fill.background()
        strip.shadow.inherit = False
    return slide


def textbox(slide, text, *, left, top, width, height=None, size=20, color=None,
          bold=False, font=SANS, align=PP_ALIGN.LEFT, spacing=1.2):
    """One text box. Returns the shape so its id can be animated."""
    color = INK if color is None else color
    box = slide.shapes.add_textbox(left, top, width, height or Inches(1))
    frame = box.text_frame
    frame.word_wrap = True
    for index, line in enumerate(str(text).split("\n")):
        para = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        para.alignment = align
        para.line_spacing = spacing
        run = para.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font
    return box


def rule(slide, *, top, left=MARGIN, width=RULE_W, color=None):
    """A short accent rule under a heading."""
    color = CYAN if color is None else color
    bar = slide.shapes.add_shape(1, left, top, width, Emu(38100))
    bar.name = RULE_NAME          # verify() finds rules by this name: text must not cross one
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    bar.shadow.inherit = False
    return bar


def heading(slide, text, *, kicker=None, size=38, top=None, color=None):
    """Standard slide head: kicker, title, accent rule."""
    color = CYAN if color is None else color
    if kicker:
        textbox(slide, kicker.upper(), left=MARGIN, top=Inches(0.72), width=BODY_W,
              height=Inches(0.32), size=12, color=color, bold=True, spacing=1.0)
    y = top or Inches(1.18)
    textbox(slide, text, left=MARGIN, top=y, width=BODY_W, size=size, color=INK,
          bold=True, spacing=1.06)
    lines = str(text).count("\n") + 1
    rule(slide, top=y + Inches(0.60 * lines + 0.28), color=color)


def slide_number(slide, value):
    """Slide number, bottom right. An explicit height, because the 1in default would
    hang past the bottom edge and make the layout audit warn on every slide."""
    textbox(slide, str(value), left=Inches(12.3), top=Inches(6.88), width=Inches(0.6),
          height=Inches(0.3), size=11, color=DIM, align=PP_ALIGN.RIGHT)


def bullets(slide, items, *, top, size=19, gap=0.86, left=None, width=None,
            color=None):
    """A stack of lines, each its own shape so each animates on its own click."""
    color = INK if color is None else color
    left = MARGIN if left is None else left
    width = BODY_W if width is None else width
    # An EXPLICIT height, because the 1in default hangs past the bottom edge when the
    # last item sits low on the slide -- the box renders nothing there, but it clips
    # against the slide boundary and the bounds check reports it. The gap is the natural
    # height: it is the room the item was allotted.
    height = Inches(max(gap, 0.32))
    return [textbox(slide, item, left=left, top=top + Inches(gap * i), width=width,
                  height=height, size=size, color=color)
            for i, item in enumerate(items)]


def figure(slide, value, label, *, left, top, color=None, width=STAT_W):
    """A measured figure with its caption. Two shapes, returned as a pair."""
    color = INK if color is None else color
    big = textbox(slide, value, left=left, top=top, width=width, height=Inches(0.92),
                size=40, color=color, bold=True, spacing=1.0)
    small = textbox(slide, label, left=left, top=top + Inches(0.86), width=width,
                  height=Inches(0.82), size=15, color=DIM, spacing=1.25)
    return [big, small]


def table(slide, headers, rows, *, top, widths, left=MARGIN, mark=None, size=15,
          height=0.44, mono=True):
    """A specification grid, built from text boxes.

    Not a PowerPoint table: a real table re-imposes its own banded fills over a dark
    surface and is awkward to position against hand-placed text. `mark` highlights one
    row -- one, because a comparison that emphasises everything emphasises nothing -- and
    ONLY when the speaker says why in the same breath: a reviewer asked "why is this row
    a different colour?" on four slides of one deck.

    `mono=False` for PROSE cells. Monospace is for identifiers; a column of sentences in
    monospace beside a sans label column read as "alternating colours" to a reviewer.
    """
    shapes = []
    x = left
    for header, width in zip(headers, widths):
        textbox(slide, header.upper(), left=x, top=top, width=width, height=Inches(0.32),
              size=11, color=CYAN, bold=True, spacing=1.0)
        x += width

    hairline = slide.shapes.add_shape(1, left, top + Inches(0.36),
                                     sum(int(w) for w in widths), Emu(12700))
    hairline.fill.solid()
    hairline.fill.fore_color.rgb = LINE
    hairline.line.fill.background()
    hairline.shadow.inherit = False

    y = top + Inches(0.50)
    for index, row in enumerate(rows):
        x = left
        for column, (cell, width) in enumerate(zip(row, widths)):
            if index == mark:
                colour, bold = CYAN, column == 0
            else:
                colour, bold = (INK if column == 0 else DIM), False
            box = textbox(slide, cell, left=x, top=y, width=width, height=Inches(height),
                        size=size, color=colour, bold=bold,
                        font=SANS if column == 0 or not mono else MONO, spacing=1.0)
            if column == 0:
                shapes.append(box)
            x += width
        y += Inches(height)
    return shapes


def terminal(slide, lines, *, top, height, left=MARGIN, width=Inches(11.0), size=15):
    """A terminal block holding COMMANDS.

    Commands, not source code: a command is one line, it is what the audience will
    retype, and both demo cards carry the full set. Five lines of Python would be
    unreadable from the back of a room.
    """
    card = slide.shapes.add_shape(1, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = TERM
    card.line.color.rgb = LINE
    card.line.width = Pt(1)
    card.shadow.inherit = False

    frame = card.text_frame
    frame.word_wrap = True
    frame.margin_left = Inches(0.28)
    frame.margin_top = Inches(0.16)
    for index, (kind, text) in enumerate(lines):
        para = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        para.alignment = PP_ALIGN.LEFT
        para.line_spacing = 1.32
        run = para.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.name = MONO
        run.font.color.rgb = {"cmd": INK, "note": DIM, "out": MINT, "alt": ROSE}[kind]
    return card


# ── charts ────────────────────────────────────────────────────────────────────
# DRAWN AS VECTOR SHAPES, not embedded images: a projector rescales the deck, and a
# rasterised chart is the thing that goes soft at the back of a room. Shapes also keep
# the chart on the signed-off palette by construction rather than by a colour-matching
# pass in another tool.
#
# COLOUR IS CONSTRAINED BY MEASUREMENT, NOT TASTE. The deck palette was fed to a
# contrast/CVD validator on the dark slide surface. Two results decided the rules below:
#
#   CYAN vs DIM   CVD separation dE 12.1 (deutan) -- PASSES. This is the pair used for
#                 every single-series chart: cyan is the subject, dim is context.
#   MINT vs ROSE  CVD separation dE 7.7 (deutan) -- in the 6-8 band, which is legal ONLY
#                 with a second, non-colour channel. So every mint/rose mark in this deck
#                 carries a TEXT LABEL beside it. A red/green colourblind viewer reads the
#                 word, not the hue.
#
# The palette also fails a strict categorical check (the lightness band, and DIM's chroma
# floor). That is expected and not a defect here: DIM is deliberately recessive context,
# and nothing in this deck is a four-series categorical chart. These are single-series
# comparisons and status marks, which is what the palette was designed for.


def bars(slide, rows, *, left, top, width, height, unit="", bar_h=0.46, gap=0.30):
    """A horizontal bar chart. `rows` is [(label, value, colour, value_text), ...].

    HORIZONTAL, because every label here is a phrase rather than a short code, and
    horizontal bars give labels a full line instead of rotating them.

    Bars start at a common left edge and are scaled to the largest value, so length is
    the only thing carrying magnitude. Each bar is directly labelled with its value --
    with two or three bars a separate axis costs more attention than it returns.
    """
    biggest = max(r[1] for r in rows) or 1
    label_w = Inches(2.7)
    track_w = width - label_w - Inches(1.5)

    shapes = []
    y = top
    for label, value, colour, value_text in rows:
        textbox(slide, label, left=left, top=y + Inches(0.04), width=label_w,
              height=Inches(bar_h), size=16, color=INK, spacing=1.0)

        # The track: where the bar would reach at full scale. It makes a short bar read
        # as short rather than as an unexplained gap.
        track = slide.shapes.add_shape(1, left + label_w, y + Inches(0.06),
                                       track_w, Inches(bar_h - 0.12))
        track.fill.solid()
        track.fill.fore_color.rgb = RAISED
        track.line.fill.background()
        track.shadow.inherit = False

        bar_w = Emu(max(int(track_w * (value / biggest)), int(Inches(0.06))))
        bar = slide.shapes.add_shape(1, left + label_w, y + Inches(0.06),
                                     bar_w, Inches(bar_h - 0.12))
        bar.fill.solid()
        bar.fill.fore_color.rgb = colour
        bar.line.fill.background()
        bar.shadow.inherit = False
        shapes.append(bar)

        textbox(slide, value_text + unit, left=left + label_w + bar_w + Inches(0.16),
              top=y + Inches(0.02), width=Inches(1.9), height=Inches(bar_h),
              size=16, color=colour, bold=True, font=MONO, spacing=1.0)
        y += Inches(bar_h + gap)
    return shapes


def line_chart(slide, points, *, left, top, width, height, y_max=None, colour=None):
    """A line chart from (x, y) pairs, drawn as connected segments.

    Built from thin rectangles rotated between consecutive points rather than a freeform:
    python-pptx has no freeform builder that survives a round-trip reliably, and segments
    are exact. With ten points the joins are invisible at projector distance.

    The first and last points are labelled and nothing between them is, because the
    message is the fall from one to the other -- a number on every point would bury it.
    """
    colour = CYAN if colour is None else colour
    y_max = y_max or max(p[1] for p in points)
    x_min, x_max = points[0][0], points[-1][0]
    span = (x_max - x_min) or 1

    def place(point):
        x, y = point
        return (left + Emu(int(width * (x - x_min) / span)),
                top + Emu(int(height * (1 - y / y_max))))

    # Baseline and left axis, both recessive: the data is the subject.
    for x0, y0, w, h in ((left, top + height, width, Emu(12700)),
                         (left, top, Emu(12700), height)):
        axis = slide.shapes.add_shape(1, x0, y0, w, h)
        axis.fill.solid()
        axis.fill.fore_color.rgb = LINE
        axis.line.fill.background()
        axis.shadow.inherit = False

    import math
    for start, end in itertools.pairwise(points):
        x1, y1 = place(start)
        x2, y2 = place(end)
        dx, dy = int(x2) - int(x1), int(y2) - int(y1)
        length = max(int(math.hypot(dx, dy)), 1)
        seg = slide.shapes.add_shape(1, Emu(int(x1)), Emu(int(y1) - 12700),
                                     Emu(length), Emu(25400))
        seg.rotation = math.degrees(math.atan2(dy, dx))
        seg.fill.solid()
        seg.fill.fore_color.rgb = colour
        seg.line.fill.background()
        seg.shadow.inherit = False

    marks = []
    for point in (points[0], points[-1]):
        x, y = place(point)
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Emu(int(x) - 50800),
                                     Emu(int(y) - 50800), Emu(101600), Emu(101600))
        dot.fill.solid()
        dot.fill.fore_color.rgb = colour
        dot.line.color.rgb = SLATE          # a surface ring, so the dot reads off the line
        dot.line.width = Pt(1.5)
        dot.shadow.inherit = False
        marks.append(dot)
    return marks


def quadrant(slide, items, *, left, top, width, height, x_label, y_label):
    """A positioning plot: two axes, one dot per item, every dot directly labelled.

    `items` is [(name, x_fraction, y_fraction, colour), ...] with fractions in 0..1.
    Fractions rather than raw values, because the two axes are in different units and
    the point being made is relative position, not a readable coordinate. The axis ends
    are labelled low/high for the same reason.

    Every dot is labelled, so identity never depends on colour -- which is what makes
    the emphasis colour safe to use on one of them.
    """
    for x0, y0, w, h in ((left, top + height, width, Emu(12700)),
                         (left, top, Emu(12700), height)):
        axis = slide.shapes.add_shape(1, x0, y0, w, h)
        axis.fill.solid()
        axis.fill.fore_color.rgb = LINE
        axis.line.fill.background()
        axis.shadow.inherit = False

    textbox(slide, x_label, left=left, top=top + height + Inches(0.16), width=width,
          height=Inches(0.26), size=12, color=DIM, align=PP_ALIGN.CENTER, spacing=1.0)
    textbox(slide, y_label, left=left - Inches(0.95), top=top + height / 2 - Inches(0.6),
          width=Inches(0.9), height=Inches(1.2), size=12, color=DIM,
          align=PP_ALIGN.RIGHT, spacing=1.1)

    marks = []
    for name, fx, fy, colour in items:
        cx = left + Emu(int(width * fx))
        cy = top + Emu(int(height * (1 - fy)))
        size = Inches(0.22)
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - size / 2, cy - size / 2,
                                     size, size)
        dot.fill.solid()
        dot.fill.fore_color.rgb = colour
        dot.line.color.rgb = SLATE
        dot.line.width = Pt(1.5)
        dot.shadow.inherit = False
        marks.append(dot)
        # LABELS SIT BESIDE THE DOT, VERTICALLY CENTRED ON IT -- never above or below.
        # Stacking labels vertically makes every dot's label a candidate to collide with
        # the next dot's, with the axis caption, and with the plot edge; two earlier
        # versions of this function chased exactly those collisions around the slide.
        # Beside the mark, the only constraint left is that dots differ in height, which
        # the caller controls directly.
        textbox(slide, name, left=cx + Inches(0.18), top=cy - Inches(0.16),
              width=Inches(1.7), height=Inches(0.32), size=13,
              color=INK if colour is CYAN else DIM, bold=colour is CYAN,
              spacing=1.0)
    return marks


def video(slide, name, *, left, top, width, height, folder=None):
    """Embed a recorded demonstration, with its last frame as the poster.

    THE POSTER IS THE FINAL FRAME, not the first. A slide that opens on an empty prompt
    looks like something failed to load; one that opens on the finished session reads as
    a result, and still makes sense if the video is never played -- which is what happens
    when a deck is read as a PDF.

    A missing file degrades to a labelled placeholder rather than raising, so the deck
    still builds on a machine where the recordings have not been made.
    """
    folder = pathlib.Path(folder or VIDEO_DIR)
    movie, poster = folder / f"{name}.mp4", folder / f"{name}.png"
    if not (movie.exists() and poster.exists()):
        box = slide.shapes.add_shape(1, left, top, width, height)
        box.fill.solid()
        box.fill.fore_color.rgb = TERM
        box.line.color.rgb = ROSE
        box.shadow.inherit = False
        textbox(slide, f"[ recording missing: pitch/video/{name}.mp4 ]",
              left=left, top=top + height / 2, width=width, height=Inches(0.4),
              size=16, color=ROSE, align=PP_ALIGN.CENTER, font=MONO)
        return box

    # FITTED TO THE BOX, ASPECT PRESERVED. Each recording is cropped to its own content,
    # so the four videos have four different shapes; a fixed box would stretch three of
    # them. The caller gives the space available and the video is centred inside it.
    from PIL import Image
    native_w, native_h = Image.open(poster).size
    scale = min(width / native_w, height / native_h)
    draw_w, draw_h = int(native_w * scale), int(native_h * scale)
    shape = slide.shapes.add_movie(
        str(movie), left + int((width - draw_w) / 2), top + int((height - draw_h) / 2),
        Emu(draw_w), Emu(draw_h),
        poster_frame_image=str(poster), mime_type="video/mp4")
    return shape


def build(slides: list, out: pathlib.Path) -> pathlib.Path:
    """Render `slides` -- a list of functions taking a Presentation -- and save.

    Refuses to build when a talk has rebranded by reassigning the palette names it
    imported rather than calling `palette()`. Those two look identical in a build script
    and behave completely differently: only the second reaches the primitives' defaults,
    so the first produces a deck in two palettes at once. The slide functions carry their
    module's namespace, which is what makes the check possible at all.
    """
    if slides:
        caller = slides[0].__globals__
        drift = [name for name in _PALETTE
                 if name in caller and caller[name] != globals()[name]]
        if drift:
            raise ValueError(
                f"palette names reassigned instead of overridden: {', '.join(drift)}.\n"
                f"Reassigning after `from deckkit.deck import *` rebinds only this "
                f"module's names; the engine's defaults are unchanged, so the deck comes "
                f"out in a mix of both palettes.\n"
                f"Call deck.palette({drift[0]}=...) instead, then re-read the values back "
                f"if the build script needs them.")

    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    for index, make in enumerate(slides, start=1):
        make(prs)
        # STAMPED HERE, NOT INSIDE EACH SLIDE FUNCTION. The numbers used to be literals in
        # the twenty-one functions, so removing one slide meant editing every number after
        # it -- and getting one wrong is invisible until someone in the audience refers to
        # a slide by number. Position is the only correct source for this.
        slide_number(prs.slides[len(prs.slides) - 1], index)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out


# GLYPH WIDTHS, in em, roughly Helvetica Neue's. A single average for all text was
# wrong in both directions: "Mariam Abdelkader" in 15pt bold -- wide capitals, M, m, A --
# was estimated as one line and PowerPoint wrapped it onto the title below, while a
# heading full of i, t and l was estimated as two lines and never wrapped. Per-character
# widths fix both; bold is ~6% wider; monospace is a flat 0.6.
_NARROW, _SEMI, _WIDE = set("iljI!|.,:;'`"), set("ftr()[]{}-/\\\"*"), set("mwMW@%")
_INSETS = Inches(0.2)        # PowerPoint's default text-frame inset, 0.1in each side


def _is_mono(run) -> bool:
    name = (run.font.name or "").lower()
    return any(m in name for m in ("menlo", "mono", "courier", "consolas"))


def _em(text: str, *, bold: bool, mono: bool) -> float:
    """Estimated width of `text`, in em."""
    if mono:
        return 0.6 * len(text)
    total = 0.0
    for ch in text:
        if ch == " " or ch in _NARROW:
            total += 0.28 if ch == " " else 0.25
        elif ch in _SEMI:
            total += 0.34
        elif ch in _WIDE:
            total += 0.86
        elif ch in "—":
            total += 1.0
        elif ch.isdigit() or ch in "$–·+=<>~#&?":
            total += 0.56
        elif ch.isupper():
            total += 0.68
        else:
            total += 0.54
    return total * (1.06 if bold else 1.0)


def _wrapped(text: str, width_in: float, pt: float, *, bold: bool = False,
             mono: bool = False) -> int:
    """Lines needed to set `text` in `width_in` inches, wrapping at WORDS as
    PowerPoint does; a word wider than the line breaks across lines."""
    to_in = pt / 72
    space = _em(" ", bold=bold, mono=mono) * to_in
    lines, used = 1, 0.0
    for word in text.split(" "):
        w = _em(word, bold=bold, mono=mono) * to_in
        if used and used + space + w > width_in:
            lines, used = lines + 1, w
        else:
            used = w if not used else used + space + w
        while used > width_in:
            lines, used = lines + 1, used - width_in
    return lines


def _extent(shape) -> tuple[int, int, float]:
    """(estimated text height in EMU, lines, largest point size) for one text box."""
    lines, biggest, height = 0, 0.0, 0
    usable = max(int(shape.width) - int(_INSETS), int(Inches(0.3)))
    for para in shape.text_frame.paragraphs:
        text = "".join(run.text for run in para.runs)
        spacing = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
        pt = max((r.font.size.pt if r.font.size else 18) for r in para.runs) if para.runs else 18
        biggest = max(biggest, pt)
        if not text.strip():
            count = 1
        else:
            count = _wrapped(text, usable / Inches(1), pt,
                             bold=any(r.font.bold for r in para.runs),
                             mono=any(_is_mono(r) for r in para.runs))
        lines += count
        height += int(count * pt * 1.2 * spacing * 12700)
    # +0.05in, not +0.1in: the frame's own top inset shifts BOTH boxes' text down
    # equally, so padding the full 0.1in counted it twice and flagged clean slides.
    return height + int(Inches(0.05)), lines, biggest


def _ink_bottom(shape) -> int:
    """Where a text box's GLYPHS end, rather than its last line box: a rule sitting
    just under a title's baseline is an underline, not a strike-through."""
    _height, lines, pt = _extent(shape)
    para = shape.text_frame.paragraphs[-1]
    spacing = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
    return int(shape.top + Inches(0.05) + (lines - 1) * pt * 1.2 * spacing * 12700
               + pt * 1.0 * 12700)


def _collisions(prs) -> list[str]:
    """Text boxes whose WRAPPED height overlaps the next box, or runs off the slide.

    THE MEASURE IS WRAPPED HEIGHT, NOT LINE WIDTH. word_wrap is on, so a long line does
    not overflow sideways -- it wraps, and the box grows downward into whatever sits
    below. A width-only check reports clean while slides overlap.

    Estimated rather than rendered, because an exact answer needs a font renderer: line
    count from a per-font glyph advance and word wrapping, the paragraph's own line
    spacing, plus frame insets. It is a smoke alarm; `snapshot.py` renders the deck in
    PowerPoint for the real answer.

    Boxes are compared only where they overlap horizontally. Two columns side by side
    share a vertical band by design, and flagging those makes the audit useless.
    """
    problems = []
    for number, slide in enumerate(prs.slides, 1):
        boxes = []
        for shape in slide.shapes:
            if not shape.has_text_frame or not shape.text_frame.text.strip():
                continue
            needed, lines, biggest = _extent(shape)
            boxes.append((shape.top, needed, lines, biggest,
                          shape.text_frame.text[:40], shape.left,
                          shape.left + shape.width))
            if shape.top + needed > SLIDE_H:
                problems.append(
                    f"slide {number}: {shape.text_frame.text[:30]!r} extends "
                    f"{(shape.top + needed - SLIDE_H) / Inches(1):.2f}in past the bottom")
            # The right edge, checked because it was not: a table widened past the slide
            # and nothing reported it -- the audit only looked downward.
            if shape.left + shape.width > SLIDE_W + Inches(0.05):
                problems.append(
                    f"slide {number}: {shape.text_frame.text[:30]!r} extends "
                    f"{(shape.left + shape.width - SLIDE_W) / Inches(1):.2f}in past the "
                    f"right edge")
        boxes.sort()
        # EACH BOX AGAINST THE NEAREST BOX BELOW IT THAT IT OVERLAPS HORIZONTALLY -- not
        # against the next box in top order. Three figures side by side share one top, so
        # pairing by order compared each value with its neighbour and never with its own
        # label, and a value that wrapped onto its label went unreported.
        for index, upper in enumerate(boxes):
            top, needed, lines, pt, label, left, right = upper
            below = [b for b in boxes[index + 1:] if b[0] > top
                     and not (right <= b[5] or b[6] <= left)]
            if not below:
                continue
            next_top = below[0][0]
            # 0.02in of tolerance: the estimate carries about +/-0.05in, and a render of a
            # 0.01in "overlap" showed clear space between the two paragraphs.
            if top + needed > next_top + Inches(0.02):
                problems.append(
                    f"slide {number}: {label!r} ({lines} lines @{pt:.0f}pt) overlaps the "
                    f"next box by {(top + needed - next_top) / Inches(1):.2f}in")
    return problems


def _rule_crossings(prs) -> list[str]:
    """Text that a heading's accent RULE runs through.

    The collision audit compares text with text, so a rule -- a shape -- was invisible
    to it, and three slides of one deck shipped with the rule striking through the first
    line of body text or a table header. A reviewer read it as a strike-through.
    """
    problems = []
    for number, slide in enumerate(prs.slides, 1):
        rules = [s for s in slide.shapes if s.name == RULE_NAME]
        for shape in slide.shapes:
            if not shape.has_text_frame or not shape.text_frame.text.strip():
                continue
            ink_top, ink_bottom = shape.top + int(Inches(0.05)), _ink_bottom(shape)
            for bar in rules:
                horizontal = shape.left < bar.left + bar.width and bar.left < shape.left + shape.width
                if horizontal and ink_top <= bar.top <= ink_bottom:
                    problems.append(f"slide {number}: the heading rule runs through "
                                    f"{shape.text_frame.text[:34]!r}")
    return problems


def add_notes(path: pathlib.Path, notes: dict[int, str]) -> int:
    """Write speaker notes into the SAVED deck: {slide number: text}. Returns how many.

    Presenter View shows them; a deck presented from memory of a separate script drifts
    from it. Reopens and re-saves the file, so call it after build() and before verify().
    """
    prs = Presentation(path)
    for number, text in notes.items():
        if 1 <= number <= len(prs.slides):     # a surplus section is notes_check's to report
            prs.slides[number - 1].notes_slide.notes_text_frame.text = text
    prs.save(path)
    return len(notes)


def verify(path: pathlib.Path, slides: list, *, required: tuple = (),
           banned: tuple = (), static: int = 3,
           extra: list | None = None) -> int:
    """Check the saved archive for motion, register, required sections and layout.

    THE MOTION CHECK IS NOT OPTIONAL. A deck that lost its transitions or its timing tree
    is byte-different and visually identical until it is presented, and python-pptx will
    not report it -- the library never knew those elements existed. So the archive is read
    back and they are counted.

    THE REGISTER CHECK IS THE REASON THIS FILE EXISTS IN ITS CURRENT FORM. An earlier
    draft shipped anthropomorphic and dramatised headings. Both are easy to reintroduce
    while editing prose, so both are enforced here rather than remembered.
    """
    import zipfile

    problems = []
    with zipfile.ZipFile(path) as archive:
        names = sorted((n for n in archive.namelist()
                        if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
                       key=lambda s: int(re.findall(r"\d+", s)[0]))
        if len(names) != len(slides):
            problems.append(f"{len(names)} slides in the file, expected {len(slides)}")
        no_transition = []
        animated = 0
        for name in names:
            xml = archive.read(name).decode("utf-8")
            if "<p:transition" not in xml:
                no_transition.append(name.rsplit("/", 1)[-1])
            if "animEffect" in xml:
                animated += 1
        if no_transition:
            problems.append(f"no transition on: {', '.join(no_transition)}")
        if animated < len(slides) - static:
            problems.append(f"{animated} slides animate, expected at least "
                            f"{len(slides) - static}")

    # ELEMENT ORDER, checked because PowerPoint does not fail loudly on it -- it opens
    # the file as "Repaired", which is the first thing an audience sees in the title bar.
    with zipfile.ZipFile(path) as archive:
        sequence = ["cSld", "clrMapOvr", "transition", "timing"]
        for name in names:
            xml = archive.read(name).decode("utf-8")
            found = sorted((xml.index(f"<p:{e}"), e) for e in sequence if f"<p:{e}" in xml)
            actual = [e for _, e in found]
            if actual != [e for e in sequence if e in actual]:
                problems.append(f"{name.rsplit('/', 1)[-1]}: elements out of schema order "
                                f"({' then '.join(actual)}) — PowerPoint will 'repair' this")

    # CAPITALISATION, one rule: small cyan labels are upper case, body text is sentence
    # case. Shouting lead-ins had crept into six slides and read as inconsistent beside
    # the labels that are meant to be upper case.
    for number, slide in enumerate(Presentation(path).slides, 1):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    size = run.font.size.pt if run.font.size else 18
                    # Below 15pt is the small-label device (kickers, table headers) and
                    # above 24pt is display type on a title or a section marker. Both are
                    # deliberately upper case. The rule applies to body copy in between.
                    if size < 15 or size > 24:
                        continue
                    lead = re.match(r"^([A-Z][A-Z' \-,]{4,})(?:\s[—:]|$)", run.text)
                    if lead and lead.group(1).strip() not in ("PASS", "FAIL"):
                        problems.append(
                            f"slide {number}: upper-case lead-in in body text: "
                            f"{lead.group(1).strip()[:34]!r}")

    text = " ".join(shape.text_frame.text
                    for slide in Presentation(path).slides
                    for shape in slide.shapes
                    if shape.has_text_frame)
    lowered = text.lower()

    for pattern in banned:
        found = re.search(pattern, lowered)
        if found:
            problems.append(f"banned language on a slide: {found.group(0)!r}")

    missing = [section for section in required if section not in text.upper()]
    if missing:
        problems.append(f"required section absent: {', '.join(missing)}")

    # CHECKS THE ENGINE CANNOT KNOW ABOUT. A deck may require its own invariants -- that
    # one section precedes another, or that a figure matches a recording beside it. A
    # build script supplies those as callables taking (path, slides, text) and returning
    # a list of problems.
    for check in (extra or []):
        problems.extend(check(path, slides, text))

    # SHAPE BOUNDS, checked separately from text collisions. A box can sit entirely
    # inside its neighbours and still hang off the slide, which is how a 1in default
    # height on a low bullet escaped the collision audit.
    for number, slide in enumerate(Presentation(path).slides, 1):
        for shape in slide.shapes:
            if shape.left is None:
                continue
            if shape.width >= SLIDE_W and shape.height >= SLIDE_H:
                continue                      # the full-bleed background
            if (shape.left < -Inches(0.02) or shape.top < -Inches(0.02)
                    or shape.left + shape.width > SLIDE_W + Inches(0.05)
                    or shape.top + shape.height > SLIDE_H + Inches(0.05)):
                label = (shape.text_frame.text[:30] if shape.has_text_frame else
                         str(shape.shape_type))
                problems.append(f"slide {number}: {label!r} is outside the slide bounds")

    layout = _collisions(Presentation(path)) + _rule_crossings(Presentation(path))
    problems.extend(layout)

    print(f"{path}  ({path.stat().st_size // 1024} KB)")
    print(f"  slides:      {len(slides)}")
    print(f"  animated:    {animated}")
    print(f"  layout:      {'clean' if not layout else f'{len(layout)} collisions'}")
    print(f"  sections:    {'all present' if not missing else 'MISSING ' + str(missing)}")
    register_ok = not any(re.search(p, lowered) for p in banned)
    print(f"  register:    {'neutral' if register_ok else 'FAIL'}")
    print("  transitions: all" if not no_transition else f"  MISSING: {no_transition}")
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}", file=sys.stderr)
        return 1
    print("  OK — motion, register, order and layout verified in the saved file")
    return 0
