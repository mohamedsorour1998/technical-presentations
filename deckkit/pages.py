#!/usr/bin/env python3
"""deckkit.pages — the standard pages every deck carries, and the check that the
opening is in place.

    from deckkit import pages

    TEAM = [pages.Person("me.jpg", "Full Name", "Title", "WORKPLACE"), ...]
    AGENDA = [pages.Section("Overview", "what it covers", 3), ...]

    def slide_team(prs):   pages.speaker_page(prs, TEAM, photo_dir=..., heading_text=...)
    def slide_agenda(prs): pages.agenda_page(prs, AGENDA, heading_text=...)
    def slide_arch(prs):   pages.diagram_page(prs, png, kicker=..., heading_text=...)

    verify(..., extra=[pages.opening_check(AGENDA, required=..., slot_minutes=20,
                                           opening_minutes=1)])

EVERY DECK OPENS WITH A SPEAKER PAGE AND AN AGENDA, at slides 2 and 3. CLAUDE.md says
why and `opening_check` enforces it: a recommendation is fixed one deck at a time, a
check is fixed once.

PALETTE AT CALL TIME. Every colour is read from `deck` when a page is drawn, after the
talk's `deck.palette()`, never copied at import -- the rebrand-by-reassignment defect
CLAUDE.md records is exactly a value copied too early.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from deckkit import deck
from deckkit.deck import (MARGIN, MSO_SHAPE, PP_ALIGN, SLIDE_W, BODY_W, Inches,
                          animate, heading, new_slide, textbox, transition)


@dataclass(frozen=True)
class Person:
    """One presenter. `workplace` is drawn as a small upper-case label, so give it in
    capitals; `extra` is at most one more line, used only where it earns its place."""
    photo: str
    name: str
    title: str
    workplace: str
    extra: str = ""


@dataclass(frozen=True)
class Section:
    """One agenda row: a section of the talk, one line on what it covers, its minutes.
    `highlight` marks the rows the room should notice -- a live demo, the questions."""
    name: str
    detail: str
    minutes: int
    highlight: bool = False


def speaker_page(prs, people: list[Person], *, photo_dir: pathlib.Path, heading_text: str,
                 kicker: str = "the team", note: str | None = None):
    """Who is talking, and why listen to them on this subject: photograph, full name,
    title, workplace. Not a CV. Photographs must be PRE-CROPPED SQUARE on disk --
    PowerPoint stretches a non-square image in a square frame -- and a missing one
    degrades to a ring so the deck still builds."""
    slide = new_slide(prs)
    heading(slide, heading_text, kicker=kicker, size=32)
    gap = Inches(0.3)
    width = (BODY_W - gap * (len(people) - 1)) / len(people)
    diameter = Inches(1.45)
    x = MARGIN
    names = []
    for person in people:
        photo = photo_dir / person.photo
        cx = x + width / 2 - diameter / 2
        if photo.exists():
            portrait = slide.shapes.add_picture(str(photo), cx, Inches(2.35), diameter, diameter)
            portrait.auto_shape_type = MSO_SHAPE.OVAL      # writes <a:prstGeom prst="ellipse">
        else:
            portrait = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx, Inches(2.35), diameter, diameter)
            portrait.fill.solid()
            portrait.fill.fore_color.rgb = deck.RAISED
            portrait.line.color.rgb = deck.CYAN
        names.append(textbox(slide, person.name, left=x, top=Inches(3.95), width=width,
                             height=Inches(0.4), size=15, color=deck.INK, bold=True,
                             align=PP_ALIGN.CENTER, spacing=1.0))
        textbox(slide, person.title, left=x, top=Inches(4.38), width=width,
                height=Inches(0.6), size=13, color=deck.DIM, align=PP_ALIGN.CENTER,
                spacing=1.1)
        textbox(slide, person.workplace, left=x, top=Inches(5.02), width=width,
                height=Inches(0.3), size=11, color=deck.CYAN, bold=True, font=deck.MONO,
                align=PP_ALIGN.CENTER, spacing=1.0)
        if person.extra:
            textbox(slide, person.extra, left=x, top=Inches(5.38), width=width,
                    height=Inches(0.8), size=11, color=deck.DIM, align=PP_ALIGN.CENTER,
                    spacing=1.15)
        x += width + gap
    transition(slide)
    if note:
        shape = textbox(slide, note, left=MARGIN, top=Inches(6.4), width=Inches(11.0),
                        height=Inches(0.6), size=15, color=deck.DIM, spacing=1.3)
        animate(slide, [shape.shape_id])
    else:
        animate(slide, [shape.shape_id for shape in names])
    return slide


def agenda_page(prs, sections: list[Section], *, heading_text: str, kicker: str = "agenda"):
    """One row per section, in order: number, name, a one-line description, minutes.
    Drawn at once, not revealed row by row -- an agenda read in stages is slower than
    the talk it introduces."""
    slide = new_slide(prs)
    heading(slide, heading_text, kicker=kicker, size=32)
    y, step = Inches(2.3), Inches(min(0.54, 4.7 / max(len(sections), 1)))
    for index, section in enumerate(sections, start=1):
        textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.6),
                height=Inches(0.36), size=14, color=deck.CYAN, bold=True, font=deck.MONO)
        textbox(slide, section.name, left=Inches(1.8), top=y, width=Inches(3.0),
                height=Inches(0.36), size=16, color=deck.CYAN if section.highlight else deck.INK,
                bold=True, spacing=1.0)
        textbox(slide, section.detail, left=Inches(4.9), top=y + Inches(0.02),
                width=Inches(6.0), height=Inches(0.36), size=14, color=deck.DIM, spacing=1.0)
        textbox(slide, f"{section.minutes} min", left=Inches(11.0), top=y + Inches(0.02),
                width=Inches(1.2), height=Inches(0.36), size=13, color=deck.DIM,
                font=deck.MONO, align=PP_ALIGN.RIGHT, spacing=1.0)
        y += step
    transition(slide)
    return slide


def diagram_page(prs, image: pathlib.Path, *, kicker: str, heading_text: str):
    """A full-slide diagram under a COMPACT head. heading()'s rule sits at 2.06in, which
    would leave a diagram under five inches tall and its labels unreadable; this head
    ends at 1.22in. The image is fitted by its real aspect ratio -- never stretched --
    and a missing file degrades to a labelled placeholder so the deck still builds."""
    slide = new_slide(prs)
    textbox(slide, kicker.upper(), left=Inches(0.8), top=Inches(0.3), width=Inches(4),
            height=Inches(0.3), size=12, color=deck.CYAN, bold=True, spacing=1.0)
    textbox(slide, heading_text, left=Inches(0.8), top=Inches(0.62), width=Inches(11.7),
            height=Inches(0.6), size=26, color=deck.INK, bold=True, spacing=1.0)
    top, bottom = Inches(1.36), Inches(7.38)
    if image.exists():
        from PIL import Image
        with Image.open(image) as img:
            ratio = img.width / img.height
        height = bottom - top
        width = int(height * ratio)
        if width > SLIDE_W - Inches(0.6):          # never wider than the slide allows
            width = SLIDE_W - Inches(0.6)
            height = int(width / ratio)
        slide.shapes.add_picture(str(image), int((SLIDE_W - width) / 2), top, width, height)
    else:
        textbox(slide, f"{image.name} missing — render the diagram first", left=MARGIN,
                top=Inches(3.5), width=BODY_W, height=Inches(0.5), size=16, color=deck.ROSE)
    transition(slide)
    return slide


def opening_check(sections: list[Section], *, required: tuple, slot_minutes: int,
                  opening_minutes: int, speaker: str = "slide_team",
                  agenda: str = "slide_agenda"):
    """A verify(extra=...) check: slide 1 is the title, slides 2-3 are the speaker page
    and the agenda (either order), the agenda NAMES every required section, and its
    minutes plus the opening sum to the slot. `speaker`/`agenda` are the talk's slide
    function names. Prove it by breaking it -- CLAUDE.md lists three valid breaks and
    one that looks valid and is not."""
    def check(path, slides, text) -> list[str]:
        names = [fn.__name__ for fn in slides]
        if speaker not in names or agenda not in names:
            return [f"no speaker page ({speaker}) or no agenda ({agenda}): every deck "
                    "opens with both"]
        problems = []
        if set(names[1:3]) != {speaker, agenda}:
            problems.append(f"slides 2 and 3 must be the speaker page and the agenda; "
                            f"they are {names[1:3]}")
        page = deck.Presentation(path).slides[names.index(agenda)]
        shown = " ".join(s.text_frame.text for s in page.shapes if s.has_text_frame).upper()
        missing = [section for section in required if section.upper() not in shown]
        if missing:
            problems.append(f"the agenda does not name: {', '.join(missing)}")
        total = opening_minutes + sum(section.minutes for section in sections)
        if total != slot_minutes:
            problems.append(f"the agenda's minutes sum to {total}, the slot is {slot_minutes}")
        return problems
    return check
