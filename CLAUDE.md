# Technical presentations

A method and a toolkit for building technical conference talks: slides generated from a
script, demonstrations recorded as video, and every figure traceable to the command that
produced it.

**Read this before starting a talk, and follow it rather than reinventing the
decisions.** Every rule here cost a real debugging cycle or a round of review feedback.

```
deckkit/deck.py            the engine: palette, primitives, charts, motion, verification
deckkit/pages.py           the speaker page, the agenda, a diagram page, the opening check
deckkit/drawio.py          architecture diagrams as AWS reference architectures (Part 3)
deckkit/record.py          runs a demo's real commands and renders them as video
deckkit/crop_photo.py      square-crops a portrait for the speaker page
deckkit/build_to.py        builds a talk to a temporary path, leaving its committed deck alone
talks/<name>/build_deck.py one talk's constants, slides, and its own checks
talks/<name>/record_demo.py one talk's demo definitions
talks/<name>/architecture/ one talk's diagram: make_architecture.py, .drawio, .png
```

The engines know nothing about any particular presentation. **To start a new talk, copy a
talk directory, replace the constants and the slide functions, and leave `deckkit`
alone.**

```zsh
uv venv .venv-deck --python 3.13
uv pip install --python .venv-deck/bin/python "python-pptx>=1.0,<2" Pillow

.venv-deck/bin/python talks/<name>/build_deck.py       # build and verify the deck
.venv-deck/bin/python talks/<name>/record_demo.py --list
.venv-deck/bin/python talks/<name>/architecture/make_architecture.py   # needs draw.io, Part 3
```

**Every deck opens with a speaker page and an agenda** (Part 2), and the build fails
without them. An architecture slide is drawn as an AWS reference architecture (Part 3).

Dependencies stay in a **dev-only** extra. A presentation tool has no business in an
application's runtime dependencies.

---

# Part 1 · Transcribing source material

Research for a talk often starts with recorded material. This runs locally: nothing is
uploaded.

- CLI: `mlx_whisper`, an isolated global `uv` tool at `~/.local/bin/mlx_whisper`.
- Model: `mlx-community/whisper-large-v3-mlx` (~2.9 GiB, cached by Hugging Face, resident
  only while `mlx_whisper` runs).
- Audio tooling: `ffmpeg`. Apple Silicon; MLX uses the Metal GPU backend automatically.

Do not download another model unless asked, and do not install MLX or its dependencies
into another project's virtualenv.

```zsh
input="/absolute/path/to/input.mp3"
mlx_whisper "$input" \
  --model mlx-community/whisper-large-v3-mlx \
  --language en \
  --condition-on-previous-text False \
  --output-dir "$PWD/sources" \
  --output-name "${input:t:r}" \
  --output-format txt \
  --verbose False
```

**`--condition-on-previous-text False` is not optional.** Without it the decoder feeds its
own output back into the next window and loops. It still exits 0, still writes a file of
plausible length, and nothing on stderr says otherwise. One file in this repo was produced
that way and repeats a 12-word sequence 19 times.

Omit `--language en` to auto-detect. `srt`, `vtt`, `tsv`, `json` or `all` for other
formats.

## Validate a transcript

Confirm it is non-empty and does not loop **without printing its contents** — these files
can hold anything said near a microphone:

```zsh
test -s out.txt && wc -c out.txt

check() {
  tr '[:upper:]' '[:lower:]' < "$1" | tr -cs "[:alnum:]'" '\n' | grep -v '^$' \
  | awk '{w[NR]=$0}
         END {for (i=1; i<=NR-11; i++) {s=""; for (j=0;j<12;j++) s=s" "w[i+j]; c[s]++}
              m=0; for (k in c) if (c[k]>m) m=c[k]
              print (m>2 ? "FAIL: sequence occurs " m " times" : "PASS: max " m)}'
}
```

Twelve words because ordinary speech does not repeat twelve verbatim — shorter windows
fire on stock phrases. More than two occurrences because a speaker may repeat a sentence
for emphasis; a decoder loop produces tens.

**Scope:** everything runs locally, do not upload media or transcript contents, do not
modify source media, and do not print transcript contents unless asked.

---

# Part 2 · Building a presentation

The engine is `deckkit/`; each talk under `talks/<name>/` supplies only its content:

```
deckkit/deck.py                   primitives, charts, motion, build, verify
deckkit/pages.py                  the speaker page, the agenda, a diagram page, the opening check
deckkit/drawio.py                 architecture diagrams — Part 3
deckkit/record.py                 runs demo commands for real and renders them as video — Part 4
deckkit/crop_photo.py             square-crops a portrait for the speaker page
deckkit/build_to.py               builds a talk to a temporary path — Part 7
talks/<name>/build_deck.py        constants, slide functions, talk-specific checks
talks/<name>/pitch/preview/       the browser design mirror
```

**Adapt these rather than rebuilding.** Every rule below cost a real debugging cycle or
a round of review feedback.

## The shape of the work

1. **Generate the `.pptx` from a committed script, never by hand.** Someone has to fix a
   typo the night before and regenerate. A hand-built deck also lets a stale number
   survive on a slide forever; a script makes every figure traceable to the command that
   produced it.
2. **Design in the browser first.** `pitch/preview/index.html` renders the same palette,
   type scale and 16:9 geometry as HTML. A colour decision takes one reload instead of
   regenerate → open PowerPoint → squint. Get sign-off there, then port the palette
   verbatim.
3. **Self-check the saved file, then open it in PowerPoint and click through once.** XML
   that validates can still render wrong.

Dependencies go in a **dev-only** extra: `python-pptx>=1.0,<2`, `Pillow`. A presentation
tool has no business in an application's runtime dependencies.

## Structuring the argument

- **State a claim that survives contact.** Not "local models are as good as frontier
  models" — the first person who tries it finds out. Something narrower and defensible.
- **Mechanism before application.** If a demo uses quantization, explain quantization
  first. Explaining it afterwards asks the audience to accept an unexplained artefact and
  then back-fills it. `verify()` checks this ordering by slide position.
- **Limitations before the recommendation, not after.** An evaluation that presents only
  favourable results does not survive questions. Put the cost in one place, first-hand.
- **Prefer your own measured failures to borrowed ones.** A published test on someone
  else's hardware can be dismissed as their broken setup. Your own cannot.

## Every deck opens with a speaker page and an agenda — REQUIRED

Slide 1 is the title, **slide 2 is the speaker page, slide 3 is the agenda**, in every
talk and every pitch. This section used to be two bullets recommending both, and a deck
shipped with neither until a reviewer asked "where is the agenda?". A recommendation gets
fixed one deck at a time; a check gets fixed once.

**The speaker page** — who is talking, and why listen to them on this subject:

- one entry per presenter: photograph (pre-cropped square), full name, **title**, and
  **workplace**. A team deck lists every member; a solo talk lists one person.
- at most **one extra line** per person, and only where it earns its place (a degree
  in progress relevant to the talk, a community role). Not a CV.
- titles and workplaces come from **one source**. If an earlier deck for the same event
  already carries them, copy that table and cite it in a comment, so the two decks
  cannot disagree about who anybody is.

**The agenda** — so the room stops tracking whether a topic is coming:

- one row per section, in presentation order, each with **a one-line description** of
  what it covers and **its minutes**. A bare list of section names is not enough.
- the rows **name every required section** of the brief, and the demo and the
  questions appear as rows of their own.
- the minutes **sum to the slot**, including the opening, the demo and the questions.
  An agenda that promises 23 minutes of a 20-minute slot is worse than none, because
  the room believes it.

**Build both with `deckkit.pages`, and enforce them in the build:**

```python
from deckkit import pages

TEAM = [pages.Person("me.jpg", "Full Name", "Senior Engineer", "EMPLOYER",
                     extra="one more line, only if it earns its place"), ...]
AGENDA = [pages.Section("Overview", "the problem and the claim", 3),
          pages.Section("Live demonstration", "what the room will see", 5, highlight=True),
          pages.Section("Questions", "the rest of the slot", 5, highlight=True), ...]

def slide_team(prs):
    pages.speaker_page(prs, TEAM, photo_dir=ROOT / "pitch" / "photos" / "square",
                       heading_text="The team", note="one sentence on how you worked")

def slide_agenda(prs):
    pages.agenda_page(prs, AGENDA, heading_text="Twenty minutes, in this order")

verify(out, SLIDES, ..., extra=[pages.opening_check(
    AGENDA, required=_REQUIRED, slot_minutes=20, opening_minutes=1)])
```

- `speaker_page` draws each person as photograph, name, title, workplace (a small
  upper-case label, so give it in capitals) and the optional extra line. A missing
  photograph degrades to a ring, so the deck still builds.
- `agenda_page` draws number, section, description and minutes, all at once. An agenda
  revealed row by row is slower than the talk it introduces, so count it in `static=`.
- `opening_check` fails when slides 2–3 are not the speaker page and the agenda (either
  order), when the agenda omits a required section, or when `opening_minutes` plus the
  rows' minutes do not equal the slot. It finds the pages by slide-function name,
  `slide_team` and `slide_agenda` by default; pass `speaker=`/`agenda=` otherwise.

**Prove it by breaking it**, all three ways: move the speaker page to the end, drop a
required section from the agenda, overfill the minutes. Each must print its `FAIL`.
Swapping the speaker page and the agenda is **not** a valid break: the check allows
either order within slides 2–3, and that inert mutation has already been made once.

## Two genres, one discipline

A **conference talk** argues a claim to an audience that chose to attend. A **pitch deck**
answers an upload specification a judge will score against. They differ in what goes on a
slide; they do not differ in rigour.

| | Conference talk | Pitch deck |
|---|---|---|
| Structure | your argument, agenda early | the spec's sections, in the spec's order |
| Required sections | what you promised | what the brief names — miss one and it fails |
| Figures | measured, first-hand | measured, or tagged as a plan |
| Limitations | a slide of their own, before the recommendation | woven in, still stated |

**Distinguish a measurement from a plan.** A pitch deck carries figures that have not
happened yet — planned pricing, a roadmap step, a target. Tag those on the slide
(`PLANNED`) rather than presenting them as fact. A judge who spots one undeclared
projection discounts every other number.

**Answer the brief in the brief's own terms.** If the upload spec names nine sections,
the deck has those nine and `_REQUIRED` lists them, so the build fails rather than the
submission.

## Content rules

- **No source code on a slide.** Nobody reads five lines off a projector in sixty
  seconds, and asking them to spends their attention on parsing instead of on the
  argument. State the idea in English. *Commands* are different when the audience will
  retype them — but if nothing is typed in the talk and there are no handouts, a snippet
  on a slide is asking the room to copy something they have no use for.
- **No per-person slides** in a team presentation. A slide headed with one name invites
  "so what did the others do" and makes a team read as individuals who worked separately.
  One combined team slide with photographs is different, and good.
- **Name real identifiers, not invented labels.** If a slide says a service is called
  `planner`, someone who opens the repository should find `planner`.
- **Every number traceable.** One constants block, each figure annotated with the command
  that produced it. Re-run those before presenting.
- **Budget the clock against the whole slot**, including demonstrations and questions.
  Twenty minutes of slides plus an eight-minute demo does not fit in thirty.

## Register — technical, neutral, professional

Enforced by `verify()`, because both of these are easy to reintroduce while editing
prose and both shipped in an early draft:

- **No anthropomorphism.** A model does not lie, know, want or try. It produces output
  that either matches a specification or does not. "It worked. And it lied." is a story
  about a character; "the script returned 67, and the summary reported 42" is a finding.
- **No dramatised headings.** "And nobody noticed", "the output was wrong", "plainly" —
  each is a narrator's voice. A finding stated flatly cannot be accused of overstating.

## Typography — one rule, applied everywhere

Reviewers read inconsistent capitalisation as carelessness, and they are right to.

| Size | Case | What it is |
|---|---|---|
| under 15pt | UPPER CASE | kickers, table headers, small labels |
| 15–24pt | Sentence case | all body copy, always |
| over 24pt | either | display type on a title or section marker |

Upper-case lead-ins in body text (`CAPACITY OVER THROUGHPUT — …`) read as shouting and
clash with the labels that are *meant* to be upper case. `verify()` fails the build on
any it finds.

## Colour — red means something failed

```python
VOID   = RGBColor(0x0A, 0x0C, 0x10)   # deepest surface, section markers
SLATE  = RGBColor(0x14, 0x18, 0x1F)   # the standard slide surface
RAISED = RGBColor(0x1C, 0x22, 0x30)   # cards and panels
TERM   = RGBColor(0x07, 0x09, 0x0C)   # terminal blocks and video background
LINE   = RGBColor(0x2A, 0x32, 0x42)   # hairlines
INK    = RGBColor(0xE8, 0xED, 0xF4)   # primary text — off-white, NEVER pure white
DIM    = RGBColor(0x8A, 0x94, 0xA6)   # secondary text
CYAN   = RGBColor(0x4F, 0xD1, 0xC5)   # ALL structure: kickers, rules, identifiers
ROSE   = RGBColor(0xFF, 0x6B, 0x6B)   # a state that actually failed
MINT   = RGBColor(0x4A, 0xDE, 0x80)   # a state that actually succeeded
SANS, MONO = "Helvetica Neue", "Menlo"
```

- **Dark**, because the viewer's brightness is unknown and it reads as instrumentation
  rather than a corporate template. Off-white, never pure white: white glares.
- **Rose is reserved.** An honest caveat is not a failure. Colouring "the measured cost
  of this choice" red turned even-handedness into an alarm; a whole paragraph in red
  drowned out the two marks on the slide that carried an actual state. In a finished
  deck rose should appear two or three times, total.
- **Do not colour-code a choice as good versus bad.** Two columns labelled in rose and
  mint say "wrong" and "right". Dim and cyan say "the other option" and "the one
  selected", which is what you mean.
- **Identifiers go in mono** — service names, filenames, flags. They are code.

### Rebranding a talk — use `palette()`, never reassignment

A talk may need its own brand colours. Set them on the engine:

```python
from deckkit import deck
from deckkit.deck import *

deck.palette(SLATE=RGBColor(0x17, 0x1D, 0x1B),   # the brand surface
             INK=RGBColor(0xF1, 0xEC, 0xDD))
SLATE, INK = deck.SLATE, deck.INK                 # re-read if the script needs them
```

**Do not rebrand by reassigning the names you imported.** `from deckkit.deck import *`
copies values; rebinding `SLATE` in a build script leaves the engine's own `SLATE`
untouched, so every primitive that falls back to a default keeps the old colour. The
first deck to try it came out with brand colours where a colour was passed explicitly and
engine colours everywhere else — a mix nobody would choose, and one that survives a
read-through because it looks deliberate. `build()` now refuses to run when it detects
this, and every primitive resolves its palette default at call time.

**Keep the validated accents unless you re-validate.** CYAN, MINT and ROSE were measured
against the default surface. Changing the surface or an accent invalidates those figures
— re-run the validator rather than assuming they carry over.

### Validate the palette, do not eyeball it

Run a contrast/CVD validator against the actual surface before shipping a chart palette.
Measured for this palette on `#14181F`:

- **cyan vs dim — ΔE 12.1 deutan, passes.** Safe for single-series charts.
- **mint vs rose — ΔE 7.7 deutan, marginal.** Legal only with a second, non-colour
  channel, so **every mint/rose mark carries a text label.** A red/green
  colourblind viewer reads the word, not the hue.

The palette deliberately fails a strict *categorical* check — DIM is low-chroma on
purpose. That is fine as long as nothing is a four-series categorical chart. If a talk
needs one, take the hues from a validated categorical ramp instead.

## Layout

16:9 at `Inches(13.333) × Inches(7.5)` — set it explicitly, the default is 4:3.

Use the **blank layout** (`prs.slide_layouts[6]`) and build every text box by hand. The
placeholder layouts fight explicit positioning: a title placeholder re-centres itself and
cannot be moved reliably across PowerPoint and Keynote.

```python
MARGIN, BODY_W = Inches(1.1), Inches(11.1)
```

Standard furniture: a small cyan **kicker** in caps, a bold **heading**, a short accent
**rule**, then content. A colour band down the left edge marks section slides.

- Hoist `Inches(...)` values used as function defaults to module constants — ruff's
  `B008` forbids a call in an argument default, and it is right to.
- **Give every text box an explicit height.** The 1in default hangs past the slide edge
  when a box sits low, and the bounds check reports it.

## Charts — draw them, do not embed images

Vector shapes, because a projector rescales the deck and a rasterised chart goes soft.
Shapes also keep the chart on the signed-off palette by construction rather than by a
colour-matching pass in another tool. `deckkit/deck.py` has three chart helpers; they cover
almost every chart a technical talk needs.

### Pick the form from the data's job — colour comes last

Most bad charts pick colour first. Decide what the data has to do, then the form, then
the marks, and only then the colour:

| The data's job | Form | Helper |
|---|---|---|
| two or three magnitudes compared | horizontal bars, directly labelled | `_bars` |
| change over a run | a line, first and last points labelled | `_line` |
| relative standing on two axes | a positioning plot, every dot labelled | `_quadrant` |
| specifications side by side | a grid built from text boxes | `_rows` |
| one headline figure | a stat block — **not a chart** | `_figure` |

If the answer is one number, a stat block beats any chart. A bar chart of one bar is a
number with decoration.

### `_bars` — magnitude

Horizontal, because labels here are phrases and horizontal bars give each a full line
instead of rotating it. Bars start at a common left edge and scale to the largest value,
so **length is the only thing carrying magnitude**.

- Draw a recessive **track** behind each bar showing where full scale would reach. It
  makes a short bar read as short rather than as an unexplained gap.
- **Direct-label each bar with its value** and skip the axis. With two or three bars an
  axis costs more attention than it returns.
- Give the bar a minimum width so a tiny value is still a visible mark.

Reach for it on a ratio claim — `1.1 GB → 331 MB`, or `359 s of audio → 55 s to process`.
Two bars make the ratio the first thing the eye gets, instead of asking the reader to
divide two printed numbers.

### `_line` — change over a run

Built from thin rectangles rotated between consecutive points, not a freeform:
`python-pptx` has no freeform builder that survives a round trip reliably, and segments
are exact. At projector distance the joins are invisible.

- **Label the first and last points only.** The message is the fall from one to the
  other; a number on every point buries it.
- Put a **surface-coloured ring** on the end markers so they read off the line.
- Baseline and axis in `LINE`, recessive.

Plot a curve when its **shape** carries something a start-and-end pair of numbers hides —
a training loss that falls steeply and then plateaus is a caveat the audience can see
rather than one they have to take on trust.

### `_quadrant` — relative standing

Two axes, one dot per item, **every dot directly labelled**, so identity never depends on
colour. That is what makes it safe to colour one dot as the selected option.

- Use **fractions, not raw values**, when the axes are in different units. Exact
  coordinates would be false precision; the point is relative position. Label the axis
  ends low→high and put the real numbers in a table beside the plot.
- **Labels go beside the dot, vertically centred** — never above or below. Stacking them
  vertically makes every label a candidate to collide with the next dot, the axis caption
  and the plot edge; two versions of this chased those collisions around the slide before
  side placement removed the class of problem.
- Space the dots apart **vertically** in the caller; that is the only constraint side
  labels leave you.

### `_rows` — a specification grid

Text boxes, not a real PowerPoint table: a table re-imposes its own banded fills over a
dark surface and is awkward to position against hand-placed text. A hairline under the
header does the work a border would.

**Highlight exactly one row.** A comparison that emphasises everything emphasises nothing.

### Marks and anatomy

- Thin marks, recessive axes and gridlines. The data is the subject.
- **Text wears text colours** — values and labels in ink or dim, never the series colour.
  A coloured mark beside them carries the identity.
- A single series needs no legend; the title names it.
- Watch the **right edge**. A grid widened past the slide went unreported until the
  bounds check covered all four sides, not just the bottom.

### The one exception — an architecture diagram

Charts are drawn as shapes. An **architecture diagram** is the one slide that embeds an
image, styled as an AWS reference architecture with the official icons, built by
`deckkit/drawio.py` and placed by `pages.diagram_page`. The whole method is **Part 3**.

### Render it and look at it

The validator checks colour, not layout. If the deck cannot be rendered locally — no
LibreOffice, and PowerPoint's subscription dialog blocks scripted export — say so plainly
and have the human click through, rather than claiming the charts are verified.

## Photographs

**Pre-crop to square on disk.** CSS crops with `object-fit: cover`; PowerPoint has no
equivalent and *stretches* a non-square image in a square frame. A stretched face is the
one defect an audience notices instantly.

Bias a portrait crop upward — take ~12% of the surplus off the top and the rest off the
bottom. A centre crop on a tall photograph cuts the top of the head off. `deckkit/crop_photo.py`
does this; run it on the source and rebuild.

Circular masks are `auto_shape_type = MSO_SHAPE.OVAL` on the picture, which writes
`<a:prstGeom prst="ellipse">` — verify it in the saved XML rather than assuming. Degrade
to initials when the file is missing, so the deck still builds without the photograph.

## Motion — the part with no API

`python-pptx` cannot do transitions or animations: `dir(slide)` exposes nothing matching
`trans` or `anim`. It models shapes and text, not the timing tree. Both live in the
slide's raw XML, which it *does* expose.

**A slide's children are ordered `cSld, clrMapOvr, transition, timing`, and the order is
not advisory.** Get it wrong and PowerPoint opens the file as **"Repaired"** — which the
audience reads in the title bar before you say a word.

This bites the moment a slide has video: `add_movie` creates a `<p:timing>` tree of its
own so the clip can play, so a transition **appended** to the slide lands after it.
Insert instead:

```python
timing = slide._element.find(P_NS + "timing")
if timing is not None:
    timing.addprevious(element)      # transition must precede timing
else:
    slide._element.append(element)
```

**Entrance animations** are one `<p:timing>` tree per slide holding click-triggered
fades. Each shape needs `<p:set>` to make it visible *plus* `<p:animEffect filter="fade">`
— without the `<p:set>` the shape is on screen from the start and the fade animates
something already visible. Copy `_animate` rather than writing it fresh; it is five
levels of nesting.

Rules that matter more than the mechanism:

- **One effect for the whole deck.** A different transition per slide is the single most
  reliable way to make a deck look amateur. Content slides wipe, section markers fade.
- **Fades only** — never fly-ins or spins.
- **Click-advanced, not timed.** The pauses are the pacing.
- **Do not animate a section marker.** Revealing one sentence in stages delays the thing
  it introduces.

---

# Part 3 · Architecture diagrams — styled as an AWS reference architecture

When a talk needs "what runs where", draw it the way AWS draws its reference
architectures: the official service icons, grouped into labelled areas inside an AWS
Cloud group, with the request's path marked as numbered steps the speaker walks in
order. It is the one slide in a deck that embeds an image, and the one where a reviewer
most readily judges the whole project by how it looks.

## Why draw.io, and why from a script

- **Why an image at all.** AWS publishes its icons as SVG and PNG, but `python-pptx`
  cannot place an SVG, and hand-placing icons and routing arrows in slide shapes
  produced a slide of text chips that a reviewer called "really bad". draw.io ships the
  whole AWS library as named stencils, routes orthogonal connectors, and renders headless
  from a CLI.
- **Why a script, not a hand-drawn file.** Coordinates in code make a layout change a
  reviewable diff, and the diagram regenerates when the system changes. The written
  `.drawio` still opens in draw.io for a hand edit; re-running the script overwrites it,
  so move a hand edit back into the script.
- **Why render at `--scale 3`.** A projector rescales the slide; at 3× the text stays
  sharp. A 1560 × 800 canvas comes out near 1.3 MB, and the deck still emails.

## Install draw.io desktop

Needed only to render; the `.drawio` file itself is plain XML.

```zsh
# When Homebrew's prefix belongs to you:
brew install --cask drawio

# Otherwise -- or to avoid touching a shared prefix -- into ~/Applications:
gh release view -R jgraph/drawio-desktop --json tagName,assets \
   --jq '.tagName, (.assets[] | select(.name | test("arm64.*zip$")) | .name)'
gh release download -R jgraph/drawio-desktop <tag> -p 'draw.io-arm64-<version>.zip' -D /tmp
ditto -x -k /tmp/draw.io-arm64-<version>.zip ~/Applications/
codesign --verify --deep --strict ~/Applications/draw.io.app && echo "signature valid"
codesign -dv ~/Applications/draw.io.app 2>&1 | grep TeamIdentifier   # UZEUFB4N53 = JGraph
~/Applications/draw.io.app/Contents/MacOS/draw.io --version
```

- **If `brew` reports its prefix is not writable, another macOS account owns it.** The
  `sudo chown -R` it suggests takes Homebrew away from that account. Install user-local
  instead; nothing shared is touched and no `sudo` is needed.
- Take the `arm64` asset on Apple silicon, `x64` or `universal` on Intel.
- `drawio.find_drawio()` looks in `~/Applications`, then `/Applications`, then `PATH`
  (`drawio`, `draw.io`), and on failure names every place it looked — so "not found" is
  never mistaken for "not installed".

## The workflow

```
talks/<name>/architecture/
    make_architecture.py     the layout, calling deckkit.drawio -- the only file you edit
    architecture.drawio      written by the script; opens in draw.io
    architecture.png         rendered at 3x; the slide embeds it
    <vendor>-mark.svg        a non-AWS logo, from the vendor's own icon package
```

```python
from deckkit import drawio
from deckkit.drawio import AWS

d = drawio.Diagram(1560, 800, theme=drawio.Theme(bg="#0B0F17", ink="#E8ECF3", ...))
d.aws_cloud("aws", 470, 70, 1080, 722, "AWS Cloud · us-east-1")    # groups FIRST
d.area("ingress", 500, 292, 1020, 150, "Ingress")
d.icon("fn", "lambda", 600, 365, "AWS Lambda", "verifies the signature", AWS["compute"])
d.edge("e2", "src", "fn", "signed webhook", points=[(440, 166), (440, 395)])
d.badge(2, 478, 404)
drawio.build(d, HERE / "architecture")    # writes .drawio, REFUSES unknown icons, renders .png
```

1. Sketch the areas and the request's path on paper first: which rows, which arrows
   cross between groups, where the numbered steps go.
2. Write the layout in `make_architecture.py` and run it.
3. **Open the PNG and look at it** (see "Render, look, repeat" below). Fix, re-render,
   look again; the reference diagram took four rounds.
4. Embed it with `pages.diagram_page` (see "Placing it on the slide" below).
5. Commit the script, the `.drawio` and the `.png` together.

`Theme` holds the diagram's colours. Use the deck's palette so the image sits *in* the
slide rather than on it: `drawio.Theme.from_deck()` reads it at call time after
`deck.palette()`. A standalone script that never imports the deck passes the hex values
explicitly.

## AWS reference-architecture conventions

| Element | Call | Rule |
|---|---|---|
| AWS Cloud | `d.aws_cloud(...)` | solid border, AWS logo in the corner; put the region in its label |
| an area of the system | `d.area(...)` | dashed, label top-left. Group by what the reader asks ("the product", "ingress"), not by AWS service category |
| an AWS service | `d.icon(id, res, x, y, title, detail, AWS[category])` | `title` is the official name (*Amazon DynamoDB*, *AWS Lambda*); `detail` is the one fact that matters here — a table name, what it verifies |
| a person | `d.person(...)` | the AWS `user` shape; label on the side no arrow leaves from |
| an external system | `d.area(...)` + `d.image(..., svg, fill=ink)` | its own group, its own mark. Take the SVG from the vendor's icon package — `npm pack @primer/octicons` for GitHub's — never retyped from memory. `fill` recolours a black mark for a dark page |
| your own code | `d.hexagon(...)` or `d.box(...)` | **no AWS icon**: borrowing one claims a managed service that is not there |
| the request's path | `d.badge(n, x, y)` | numbered circles in the accent colour, in the order the request travels. Six to nine steps is readable |

**Category colours** are AWS's, Release 16 (2023-04-28), in `drawio.AWS`. Confirmed
against AWS's icon deck and AWS Labs' `aws-icons-for-plantuml` before they went in;
re-check at `aws.amazon.com/architecture/icons` when a new release ships.

| Colour | `AWS[...]` keys |
|---|---|
| Smile `#ED7100` | `compute`, `containers` |
| Cosmos `#E7157B` | `integration`, `management` |
| Nebula `#C925D1` | `database`, `devtools` |
| Mars `#DD344C` | `security`, `frontend` |
| Orbit `#01A88D` | `ai`, `migration` |
| Endor `#7AA116` | `storage`, `iot` |
| Galaxy `#8C4FFF` | `networking`, `analytics`, `serverless` |

**A service newer than the icon set** gets its parent service's icon, with the label
carrying the precision — but look first: draw.io's library is updated more often than
people assume, and the reference diagram's AgentCore and Nova icons both existed.

## Icon names — look them up, never guess

**A wrong `resIcon` renders as a plain coloured square, and draw.io raises nothing.**
The first render of the reference diagram drew ECR that way: the name is `ecr`, not
`elastic_container_registry`. So `drawio.build()` reads every AWS name out of draw.io's
own bundle and refuses a diagram that uses one it lacks — before anything is written.

```zsh
.venv-deck/bin/python -c "import sys; sys.path.insert(0, '.'); from deckkit import drawio
print(sorted(n for n in drawio.available_icons() if 'dynamo' in n))"
```

Names that are not what you would type: `ecr`, `cloudwatch_2`,
`identity_and_access_management`, `secrets_manager`, `bedrock_agentcore`, `nova2`.

**The lookup reads two patterns, and the first alone is wrong.** Older names appear in
the bundle as literal `mxgraph.aws4.<name>`. Newer resource icons are built at runtime in
the minified sidebar as `resIcon="+d+".<name>`, so the full name never appears as one
string. A scanner reading only the literal pattern reported `bedrock_agentcore` and
`nova2` missing while both rendered correctly — caught only because it was tested against
names already known to render. **Test a detector on things known to exist, not only on
things known to be absent.**

## Layout — the rules that made it readable

Every one of these came from a render that was wrong. None of the fixes was a nudge;
each was structural.

- **Draw groups first.** Cells paint in the order they are added; a group added last
  covers everything inside it.
- **One row per area, and icons in a row share a `y`.** A 20 px offset between two
  icons turns a straight arrow into a kink.
- **One lane per arrow that crosses between groups.** Route it through the empty band
  between rows with explicit `points=`. Three arrows side by side in one gap read as a
  single tangle; the reference diagram's first render had exactly that, and the fix was
  moving a person and a row so each arrow got its own band.
- **An arrow must never cross text.** When an arrow leaves an icon's bottom, put that
  icon's label above it (`label_above=True`); give a person's label the side no arrow
  uses (`position=`).
- **Pin exits and entries** with `style="exitX=…;exitY=…;entryX=…;entryY=…"` when the
  router picks a side that crosses something. Entering a tall group at height `y`:
  `entryY = (y − group_top) / group_height`.
- **Slide a label along its arrow** with `at=` (−1 at the source, 1 at the target) to
  clear an icon or another label.
- **Where two lines must cross, let them** — jump arcs (on by default) show it as a
  crossing rather than a junction.
- **Cut an arrow that crosses the whole diagram to say one thing.** Say it in a label
  instead ("every stage writes it"). The reference diagram lost one long dashed arrow
  this way and gained a clear lane.
- **Badges beside labels, never on them**, and never over a group's title.
- **Keep node labels short enough not to wrap.** Monospace text in a narrow box wraps
  first; a job box reading `gate1 · a named reviewer` wrapped onto two lines, and the
  fix was the word `gate1` with the reviewer drawn as a person beside it.
- **Size the canvas to the slide area's aspect.** Under a compact head the area is about
  11.7 × 6.0 in, so roughly 1.95:1 — 1560 × 800 is the reference.

## Size the text for the projector, and measure it

A label's size on the slide is `px ÷ (canvas px ÷ slide inches) × 72`, which is what
`drawio.label_points(px, canvas_width_px=…, slide_width_in=…)` returns. Measured on the
reference diagram, 11.71 × 6.02 in on the slide:

| Label | Canvas px | On the slide |
|---|---:|---:|
| icon labels | 17 | 9.2 pt |
| area labels | 18 | 9.7 pt |
| arrow labels | 15 | **8.1 pt** |

The arrow labels are the smallest text in a deck and are tolerable only because the
speaker narrates every numbered step. **Do not go below them.** If a layout needs
smaller text, it has too much in it — cut a node.

## Render, look, repeat

No check can see an arrow through a label. After every render, open the PNG — an agent
reads it with its image tool, a person opens it — and look for:

- a **plain coloured square** where an icon should be (a wrong name `build()` could not
  read the library to catch);
- **arrows crossing labels**, and **badges on top of labels or group titles**;
- **parallel lines stacked in one gap**, and **kinks** from icons out of line;
- **wrapped node labels**, and anything touching a group's border.

Then render again and look again. Do not embed a diagram nobody has looked at.

## Every box is a claim

A diagram is read as evidence of how the system works, so check each box and arrow
against the system's own documentation or code, and write down in the script's
docstring what was checked and when. The reference diagram's first draft drew a database
table the system does not actually use; it was caught by checking, not by looking.

## Placing it on the slide

```python
def slide_architecture(prs):
    pages.diagram_page(prs, ROOT / "architecture" / "architecture.png",
                       kicker="architecture", heading_text="What runs where — follow the numbers")
```

- **A compact head, not `heading()`.** `heading()`'s rule sits at 2.06 in, which leaves a
  diagram under five inches tall and its labels unreadable. `diagram_page` puts the
  kicker at 0.30 in and the title at 0.62 in, and the image fills 1.36 → 7.38 in, fitted
  by its real aspect ratio and centred — never stretched.
- **A missing PNG degrades to a labelled placeholder**, so the deck builds on a machine
  without draw.io.
- **The slide has no entrance animation** — count it in `verify(static=…)`.
- **Tell the room how to read it** in the title ("follow the numbers"), and have the
  speaking script walk the numbered steps in order. Eight steps take about 1:10.
- **Keep the kicker clear of the title.** The layout audit flagged a 0.06 in overlap
  between them at 0.55 in; 0.62 in clears it.

---

# Part 4 · Recording demonstrations as video

When a demo must not run live — a committee asks for it, or the stack is too flaky to
trust on stage — record it and embed it. `deckkit/record.py` runs the real commands and
renders their real output as video.

## Render, do not screen-capture

The commands are executed and their **actual stdout** is what reaches the frames. Nothing
is typed into a script by hand. Rendering that captured output, rather than filming the
screen, buys four things:

- **Type size is chosen**, not inherited from whatever the terminal happened to be set to.
- **Nothing else is in shot** — no notification, no menu bar, no other window, no cursor.
- **The palette is the deck's**, so the video sits inside the slide instead of on top.
- **It regenerates.** If a measurement moves, re-render and the video agrees with the
  slide again. A screen capture quietly drifts out of date.

## Architecture

**Two passes.** The session records a *script* of frames first, then draws them — because
the frame height depends on the tallest moment and that is not known until the run
finishes. Drawing immediately produced a fixed 16:9 with the content stranded in the top
third and a large empty area below.

**Measure the font, never assume it.** A hardcoded 17px glyph advance was one pixel per
character too narrow at 30px Menlo (the real value is 18). Every long line wrapped about
five characters late and drew them past the right edge, losing a letter mid-word —
invisibly, in a video nobody can pause to query.

```python
def _chars_per_line() -> int:
    advance = _font().getlength("M" * 100) / 100
    return int((W - 2 * PAD_X) // advance) - 1
```

**Cache the captured output.** Rendering and running are different problems. Store each
command's stdout and true elapsed time in `bench/recorded-output.json`; `--reuse`
re-renders from it instantly. Without this, every tweak to how a frame *looks*
re-executed the commands behind it — and one of those was an agent call that took 65
seconds on a good day and thirteen minutes on the day the model server died mid-request.

**Read the reuse flag inside `run()`, not at each call site.** Threading it through as an
argument left five call sites silently re-executing, which is the opposite of the point
and cost three ten-minute hangs to notice.

## Honesty in the edit

- **Compress long waits, and say the real number on the frame.** A ninety-second training
  run played at life size is the dead air that made the demo unsuitable for the stage.
  Show a brief animated ellipsis with `actual: 1m 29s` beside it. Anything under about
  six seconds plays at its true length.
- **Say on the slide that it is a recording**, and say it aloud the first time one plays.
  An audience that works it out for itself discounts everything after it.
- **Reassemble into causal order when a tool lies about it.** OpenCode writes its final
  answer *before* the tool trace when its output is piped rather than attached to a
  terminal; interactively the order is command, result, answer. Replaying the piped order
  showed the agent answering before it looked anything up — inverting the one thing the
  recording existed to show. Group the lines by role instead.

## Embedding

```python
shape = slide.shapes.add_movie(str(movie), left, top, w, h,
                               poster_frame_image=str(poster),
                               mime_type="video/mp4")
```

- **The poster is the LAST frame, not the first.** A slide opening on an empty prompt
  looks like something failed to load; one opening on the finished session reads as a
  result — and still makes sense if the video never plays, which is what happens when
  the deck is read as a PDF or opened on a venue machine.
- **Fit to the box, preserving aspect.** Each recording is cropped to its own content, so
  several videos have several shapes; a fixed box stretches most of them. Read the
  poster's real dimensions and centre the video inside the space allowed.
- **Degrade to a labelled placeholder** when the file is missing, so the deck builds on a
  machine where the recordings were never made.
- Encode H.264, `yuv420p`, `-crf 30`, `+faststart`. Four clips totalling 40 s came to
  ~340 KB; the whole deck stayed under 1.5 MB and emails fine.

## Contingency for a video deck

There is almost nothing left to go wrong, which is the point. What remains:

| Condition | Action |
|---|---|
| a video will not play | press Escape — the poster is the final frame, so narrate the still |
| venue machine, old PowerPoint | same; bring the file on a USB stick as well as email |
| someone reaches for the volume | the recordings are silent by design; say so |

---

# Part 5 · Self-verification — not optional

A deck that silently lost its motion is byte-different and **visually identical until it
is presented**, and `python-pptx` will never report it: it never knew those elements
existed. So read the saved archive back and count them.

`verify()` in `deckkit/deck.py` runs every check below; a talk adds its own through
the `extra=` hook. Each one caught a real defect.

| Check | Why it exists |
|---|---|
| transitions and `animEffect` counted per slide | the library cannot tell you they are missing |
| **element order** `cSld, clrMapOvr, transition, timing` | wrong order makes PowerPoint open the file as "Repaired" |
| **wrapped-height** collisions | a width-only check reported clean while six boxes overlapped |
| **shape bounds**, all four edges | a table ran off the right of the slide unreported — the audit only looked down |
| banned language | anthropomorphism and dramatised headings creep back while editing prose |
| **capitalisation** in 15–24pt body text | shouting lead-ins had reached six slides |
| required sections present | a deck that reads well and omits a required topic fails the brief |
| **exposition order** by slide position | quantization must precede the demo that uses it |
| **the opening** — speaker page and agenda at slides 2–3, `pages.opening_check` | a deck shipped with neither while this file only recommended both |
| **figures vs the recording** | a slide must not contradict the video playing beside it |

One more check runs earlier, when an architecture diagram is built: `drawio.build`
refuses an icon name draw.io does not have, because a wrong one renders as a blank
square and raises nothing (Part 3).

On the layout check specifically: the question is wrapped **height**, not line width.
With `word_wrap` on, a long line does not overflow sideways — it wraps, and the box grows
**downward** into whatever sits below. Compare boxes only where they overlap
horizontally; two columns side by side share a vertical band by design, and flagging
those makes the audit cry wolf.

Then `file -b deck.pptx` should say `Microsoft OOXML`, and **open it and click through**.

## Prove a check works by breaking it

After adding a check, break the thing it guards and confirm it fails, then restore. A
check that never fires is indistinguishable from one that cannot.

```zsh
sed -i '' 's/^Q_TPS = 253 /Q_TPS = 999 /' scripts/build_deck.py
.venv-deck/bin/python scripts/build_deck.py     # expect FAIL
sed -i '' 's/^Q_TPS = 999 /Q_TPS = 253 /' scripts/build_deck.py
```

## Numbers must be traceable

Keep every figure in one constants block, each annotated with the command that produced
it, and re-run those commands before presenting.

Where a figure also appears in a recording, **check the two agree at build time** rather
than by memory — read the value out of the cached output and fail if the slide disagrees.
Throughput varies run to run, and a slide contradicting the video beside it is the one
error nobody in the room can miss.

## Timing

Budget against the **whole slot**, including questions, and verify the sum
programmatically rather than by eye:

```zsh
python3 - <<'PY'
import re, pathlib
t = pathlib.Path('pitch/REHEARSAL.md').read_text()
total = sum(int(m)*60+int(s) for _,_,m,s in
            re.findall(r'^## ([\d–\-]+) · ([^—\n]+)—\s*(\d+):(\d+)', t, re.M))
print(f"{total//60}:{total%60:02d} presenting -> {30-total/60:.1f} min Q&A")
PY
```

Measure what a demo actually takes before allocating a slot to it. A task that runs 2:59
inside a 3:30 slot is 31 seconds of speaking and a progress bar — that is what recording
it fixes.

---

# Part 6 · Deliverables and layout

```
CLAUDE.md                        this method
deckkit/deck.py                  the slide engine
deckkit/pages.py                 speaker page, agenda, diagram page, opening check
deckkit/drawio.py                architecture diagrams -> .drawio -> .png
deckkit/record.py                the demo recorder
deckkit/crop_photo.py            portrait cropping
deckkit/build_to.py              build a talk elsewhere: an open deck, an engine check
talks/<name>/
    build_deck.py                constants, slide functions, talk-specific checks
    record_demo.py               demo definitions
    architecture/
        make_architecture.py     the diagram's layout, calling deckkit.drawio
        architecture.drawio      written by the script; opens in draw.io
        architecture.png         rendered at 3x; diagram_page embeds it
        <vendor>-mark.svg        a non-AWS logo, from the vendor's own icon package
    bench/                       measured output — the source of every figure
    sources/                     research material (transcripts, notes)
    pitch/
        <Name>.pptx              the deck — videos travel inside it
        DEMO-PLAN.md             what each demonstration shows (goes to organisers)
        REHEARSAL.md             speaking script, timings, contingencies, Q&A (private)
        video/*.mp4 *.png        recordings and their poster frames
        preview/index.html       the design mirror
        photos/square/           pre-cropped 640×640 portraits
```

The preview is a **design mirror, not a source of truth**. Its CSS custom properties and
the engine's palette constants are the two places a colour lives, and they must change
together — otherwise what is on screen stops being what was signed off.

## The worked examples

**`talks/bringing-the-model-home/`** — a 30-minute conference talk given at DevOpsDays
Cairo 2026. 18 slides, four embedded recordings, charts drawn as vector shapes, and two
talk-specific `verify()` hooks. Read its `build_deck.py` for how a talk supplies content
to the engine, and `pitch/REHEARSAL.md` for how a speaking script and its timings are
kept in step with the slides.

**`talks/rosettacloud-genai-hackathon/`** — a 14-slide pitch deck answering a hackathon's
upload specification. Shows the other genre: a rebranded palette through `deck.palette()`,
a locally defined `_card_row` helper for a layout the engine does not provide, no
recordings, and required sections taken from the brief. It needed no change to the engine,
which is the point of the split.

**`talks/devops-hackathon-final/`** — a 17-slide finals pitch deck, twenty minutes including
the demo and the questions. The reference for **the opening** (a speaker page with each
presenter's title and workplace, an agenda with minutes, `pages.opening_check`) and for
**an architecture diagram** (`architecture/make_architecture.py`: an AWS Cloud group,
three areas, fourteen AWS icons, a vendor mark, eight numbered steps). It uses the
product's own palette, so the deck matches the app shown in the live demo, and its
`pitch/REHEARSAL.md` walks the diagram's numbered steps.

**A talk may add its own helpers.** If a layout is specific to one deck, define it in that
deck's build script rather than growing the engine. Only promote something into `deckkit`
when a second talk needs it — or, like the speaker page, the agenda and the diagram, when
this method requires it of every talk. When you promote, prove the move changed nothing:
rebuild and compare the artefact itself (below).

---

# Part 7 · Working method

Lessons from this project that cost real time:

- **Encode the rule, do not fix the instance.** Capitalisation and misused red were
  corrected three times and returned each time, because only the instances were fixed.
  They stopped returning when they became build checks. If the same class of defect
  appears twice, write the check.
- **Assert that an edit matched before claiming it worked.** A replacement whose pattern
  did not match printed success anyway, and the stale text shipped onto a slide. Any
  scripted edit should `assert old in text` first.
- **Measure, do not assume, anything about rendering** — glyph advances, wrapped heights,
  aspect ratios. Every one of those assumptions was wrong at least once here.
- **Separate running from rendering** in any tool that does both, and cache the run.
- **One switch, read in one place.** A flag threaded through call sites gets missed at
  five of them.
- **When output looks reordered, check whether the tool buffers differently off a TTY**
  before assuming your own code is wrong.
- **Re-read a generated artefact after a structural change.** Deleting a slide left nine
  dangling references, one of them printed on another slide.
- **A defect that produces plausible output is the expensive kind.** The rebrand-by-
  reassignment bug shipped a deck in two palettes at once; it looked deliberate, so
  nothing flagged it until the colours were read out of the saved file. When a change
  *should* have had a visible effect, verify it did — do not infer it from the code.
- **The first reuse is the real test of an abstraction.** Splitting the engine out looked
  finished until a second deck used it, which immediately found a latent bug in how
  defaults bind. Build the second thing before believing the first one generalises.
- **Prove a refactor by comparing the artefact, not by reading the code.** Moving the
  diagram and page helpers into `deckkit` was verified by regenerating the `.drawio`
  byte-for-byte and rebuilding the deck with all 73 archive parts identical (`docProps/`
  timestamps excluded). A refactor that "looks the same" has not been checked.
- **Building a talk writes its committed deck.** Checking that an engine change leaves
  other talks building will rewrite their `.pptx` files. Build them elsewhere instead —
  `.venv-deck/bin/python -m deckkit.build_to talks/<name>/build_deck.py /tmp/x.pptx` runs
  the talk's own checks and exit code — or restore with `git checkout` afterwards.
- **Never write a deck that is open in PowerPoint.** A `~$<Name>.pptx` lock file beside it
  means it is open; a rebuild then races whatever the person saves. Use
  `deckkit.build_to` and compare the archive parts instead.
- **A same-size RED mutation can outlive its revert.** Python invalidates a cached
  `.pyc` on a change of mtime or size, so a mutation that keeps the file's length (`5` →
  `8`), reverted within the same second, leaves a cache entry that still validates. The
  next build ran the MUTATED code while the source on disk was correct, and printed a
  `FAIL` that looked like a failed restore. `deckkit.build_to` writes no bytecode for this
  reason. Prefer mutations that change length; when a revert "does not take", delete
  `__pycache__` before suspecting the edit.
- **An inert mutation reads exactly like a caught one.** A break that swapped the speaker
  page and the agenda — which the check allows — printed success, and would have been
  recorded as proof. Show that each break changes the output; if it does not, it tested
  nothing, so pick another and say so.
- **Test a detector on things known to exist, not only on things known to be absent.** The
  icon-name check caught every bad name and also rejected two good ones; only a list of
  names already rendering correctly revealed it.
- **Name where you searched before saying something is absent.** "No renderer here" means
  "not in `/Applications`, `~/Applications` or `PATH`" — say that, so the next person can
  see the shape of the hole.
- **Never take over a shared tool to install one of your own.** A package-manager prefix
  owned by another account stays theirs; install user-local (Part 3 does this for
  draw.io).
