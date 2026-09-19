# Technical presentations

A method and a toolkit for building technical conference talks: slides generated from a
script, demonstrations recorded as video, and every figure traceable to the command that
produced it.

**Read this before starting a talk, and follow it rather than reinventing the
decisions.** Every rule here cost a real debugging cycle or a round of review feedback.

```
deckkit/deck.py            the engine: palette, primitives, charts, motion, verification
deckkit/record.py          runs a demo's real commands and renders them as video
deckkit/crop_photo.py      square-crops a portrait for the speaker slide
talks/<name>/build_deck.py one talk's constants, slides, and its own checks
talks/<name>/record_demo.py one talk's demo definitions
```

The engines know nothing about any particular presentation. **To start a new talk, copy a
talk directory, replace the constants and the slide functions, and leave `deckkit`
alone.**

```zsh
uv venv .venv-deck --python 3.13
uv pip install --python .venv-deck/bin/python "python-pptx>=1.0,<2" Pillow

.venv-deck/bin/python talks/<name>/build_deck.py       # build and verify the deck
.venv-deck/bin/python talks/<name>/record_demo.py --list
```

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

A working implementation is in this repo and is the reference:

```
scripts/build_deck.py      the generator — slides, charts, motion, self-checks
scripts/record_demo.py     runs demo commands for real and renders them as video
scripts/crop_photo.py      square-crops a portrait for the speaker slide
pitch/preview/index.html   the browser design mirror
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
- **An agenda slide early** so the audience stops tracking whether a topic is coming.
- **A separate, brief speaker slide.** Three lines answering "why listen to this person
  on this subject". Not a CV.

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

# Part 3 · Recording demonstrations as video

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

# Part 4 · Self-verification — not optional

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
| **figures vs the recording** | a slide must not contradict the video playing beside it |

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

# Part 5 · Deliverables and layout

```
CLAUDE.md                        this method
deckkit/deck.py                  the slide engine
deckkit/record.py                the demo recorder
deckkit/crop_photo.py            portrait cropping
talks/<name>/
    build_deck.py                constants, slide functions, talk-specific checks
    record_demo.py               demo definitions
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

**A talk may add its own helpers.** If a layout is specific to one deck, define it in that
deck's build script rather than growing the engine. Only promote something into `deckkit`
when a second talk needs it.

---

# Part 6 · Working method

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
