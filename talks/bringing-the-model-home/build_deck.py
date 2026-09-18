#!/usr/bin/env python3
"""Build the DevOpsDays Cairo 2026 talk. Content only — the engine is deckkit/deck.py.

    .venv-deck/bin/python talks/bringing-the-model-home/build_deck.py

This file holds what is true about THIS talk: its measurements, its slides, and the
checks that only make sense for it. Everything about how a slide is drawn, how motion is
written, and how the saved file is verified lives in deckkit/deck.py, which knows nothing
about any particular presentation.

To start another talk: copy this file, replace the constants and the slide functions,
and leave deckkit alone.

REGISTER, AND WHY IT IS ENFORCED
================================
The deck reads as a technical report. Two habits kept coming back during editing and are
now build failures rather than things to remember:

  * ANTHROPOMORPHISM. A model does not lie, know, want or try. It produces output that
    either matches a specification or does not.
  * DRAMATISED HEADINGS. "And nobody noticed", "the output was wrong", "plainly" -- each
    is a narrator's voice. A finding stated flatly cannot be accused of overstating.

EVERY NUMBER WAS MEASURED ON THE PRESENTING MACHINE
===================================================
MacBook Air, Apple M4, 16 GiB, macOS 26.6. Each constant carries the command that
produced it; raw output is committed under bench/. Figures for other vendors are
vendor-published specifications, labelled as such on the slide.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# The engine is a package at the repository root, two levels up from a talk.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from deckkit import deck
from deckkit.deck import *  # noqa: F403 — palette, geometry, primitives, build, verify

ROOT = pathlib.Path(__file__).resolve().parent
deck.VIDEO_DIR = ROOT / "pitch" / "video"

# ── measured on the presenting machine ────────────────────────────────────────
# MacBook Air · Apple M4 · 16 GiB · macOS 26.6. Re-run the benchmarks before presenting.
#   python3 scripts/bench_whisper.py     -> bench/whisper.json
#   python3 scripts/bench_lm.py          -> bench/lm.json
WHISPER_RT = 6.5           # 359 s of audio transcribed in 55.0 s wall clock
WHISPER_SECONDS = 55       # the same run, stated as elapsed time
WHISPER_GIB = 2.9          # du -sh on the Hugging Face cache
TRANSCRIPT_WORDS = 1103    # identical across two runs
HOURS_PER_100 = 15         # 100 / WHISPER_RT, rounded down

LM_GIB = 2.9               # Qwen3.5-4B-MLX-4bit on disk
LM_PEAK_GB = 2.5           # mlx_lm.generate: "Peak memory: 2.525 GB"
LM_GEN_TPS = 36            # mlx_lm.generate: "Generation: 36.063 tokens-per-sec"
LM_PROMPT_TPS = 344        # 2728 prompt tokens in ~7.94 s, from bench/server.log

# QUANTIZATION -- mlx_lm.convert, Qwen3-0.6B bf16 -> 4-bit, group size 64.
Q_BEFORE_GB = 1.1          # du -sh the bf16 cache entry
Q_AFTER_MB = 331           # du -sh models/qwen3-0.6b-4bit
Q_BITS = 4.501             # "Quantized model with 4.501 bits per weight"
Q_FACTOR = 3.4             # 1.1 GiB / 331 MiB
# THESE TWO MUST MATCH THE RECORDING ON SLIDE 9, which shows them in the model's own
# output. They vary a little run to run, so they are taken from the run that was recorded
# and verify() re-checks them against bench/recorded-output.json on every build -- a slide
# contradicting the video playing beside it is the one error nobody in the room can miss.
Q_TPS = 253                # "Generation: 8 tokens, 253.349 tokens-per-sec"
Q_PEAK_MB = 441            # "Peak memory: 0.441 GB"

# FINE-TUNING -- mlx_lm.lora on Qwen3-0.6B at 4-bit, LoRA, --mask-prompt, 8 layers.
# ONLY THE 0.6B MODEL IS TRAINED. A 4B run needs 8.7 GB and was killed by the OS when the
# inference server was also resident -- on a 16 GB machine the two do not coexist. The
# small model trains in under a minute, so it runs live and nothing has to be prepared.
# Timed three times: 42 s on an otherwise idle machine, 76 s and 89 s with other
# processes resident. The slowest is quoted -- on stage the inference server, a browser
# and a screen recorder are all loaded, so the idle figure would be the one that
# embarrasses you in front of a room.
FT_SECONDS = 90            # 100 iterations, conservative of three timed runs
FT_VAL_FROM, FT_VAL_TO = 4.167, 1.682          # first and last eval of the plotted run
FT_ADAPTER_MIB = 5.5       # du of adapters-0.6b/adapters.safetensors
FT_EXAMPLES = 53           # wc -l data/*.jsonl
FT_PEAK_GB = 1.5           # reported peak during training

# The measured validation-loss curve, eval every 10 iterations. Plotted on slide 11.
# The first value varies run to run -- the validation split is five examples and the model
# is untrained at iteration 1 -- so the curve is quoted from the run that is plotted.
# The endpoint is stable at 1.68 across runs, and the SHAPE is the point: a steep fall to
# iteration 20, then a plateau that wobbles. That plateau is the overfitting the slide
# text claims, which is why it is shown rather than asserted.
FT_CURVE = [(1, 4.167), (10, 3.202), (20, 1.858), (30, 1.936), (40, 1.919),
            (50, 1.918), (60, 1.874), (70, 1.773), (80, 1.636), (90, 1.704),
            (100, 1.682)]

# AGENT -- OpenCode 1.18.22 driving the local server. Wall clock, end to end.
AGENT_COUNT_SECONDS = 61   # a word-count question; the agent selected `wc -w`

# VENDOR-PUBLISHED SPECIFICATIONS, not measurements. Sources on the references slide.
M4_BW, M4_RAM = 120, 32            # apple.com/newsroom, 30 October 2024
M4PRO_BW, M4PRO_RAM = 273, 64
M4MAX_BW, M4MAX_RAM = 546, 128
RTX_VRAM = 32                      # nvidia.com: 32 GB GDDR7, 512-bit
STRIX_RAM, STRIX_BW = 128, 215     # amd.com: Ryzen AI Max

# Kickers that must be present, so an edit cannot silently drop a section.
_REQUIRED = (
    "SPEAKER", "CONTEXT", "AGENDA", "OPTIONS", "SELECTION", "ARCHITECTURE",
    "QUANTIZATION", "FINE-TUNING", "DEMONSTRATION 1",
    "DEMONSTRATION 2", "LIMITATIONS", "CRITERIA", "REFERENCES",
)

# Language that must not reach a slide. The first group is anthropomorphism, the second
# is dramatisation, and both were present in an earlier draft of this deck.
# Matched on WORD BOUNDARIES, not as substrings: an early version banned "lied" and
# fired on "applied", and a check that flags innocent copy is one that gets disabled.
_BANNED = (
    r"\blied\b", r"\bit lied\b", r"\bknows\b", r"\bwants to\b", r"\btried to\b",
    r"\bnobody noticed\b", r"\bthe output was wrong\b", r"\bplainly\b", r"\bcrap\b",
    r"\bsilent wrongness\b",
    r"\bdef \b", r"\bimport \b",              # source code
    r"\$1\.49", r"25 tokens per second on an M5",  # from a corrupted transcript
)

_REQUIRED = (
    "SPEAKER", "CONTEXT", "AGENDA", "OPTIONS", "SELECTION", "ARCHITECTURE",
    "QUANTIZATION", "FINE-TUNING", "DEMONSTRATION 1",
    "DEMONSTRATION 2", "LIMITATIONS", "CRITERIA", "REFERENCES",
)

# Language that must not reach a slide. The first group is anthropomorphism, the second
# is dramatisation, and both were present in an earlier draft of this deck.
# Matched on WORD BOUNDARIES, not as substrings: an early version banned "lied" and
# fired on "applied", and a check that flags innocent copy is one that gets disabled.
_BANNED = (
    r"\blied\b", r"\bit lied\b", r"\bknows\b", r"\bwants to\b", r"\btried to\b",
    r"\bnobody noticed\b", r"\bthe output was wrong\b", r"\bplainly\b", r"\bcrap\b",
    r"\bsilent wrongness\b",
    r"\bdef \b", r"\bimport \b",              # source code
    r"\$1\.49", r"25 tokens per second on an M5",  # from a corrupted transcript
)

# ── slides ────────────────────────────────────────────────────────────────────

def slide_title(prs):
    slide = new_slide(prs, band=CYAN)
    textbox(slide, "BRINGING THE\nMODEL HOME", left=MARGIN, top=Inches(1.85),
          width=BODY_W, size=58, color=INK, bold=True, spacing=1.02)
    rule(slide, top=Inches(3.85), width=Inches(2.6))
    textbox(slide, "Running production AI workloads on local hardware,\n"
                 "and deciding which workloads qualify.",
          left=MARGIN, top=Inches(4.25), width=Inches(10.4), size=23, color=DIM)
    textbox(slide, "Mohamed Sorour   ·   Senior DevOps Engineer, Vezeeta\n"
                 "DevOpsDays Cairo 2026",
          left=MARGIN, top=Inches(5.85), width=BODY_W, size=15, color=DIM)
    transition(slide, kind="fade")


def slide_speaker(prs):
    """Slide 2. A brief bio, and nothing else.

    REQUESTED SEPARATELY BY THE PROGRAMME COMMITTEE. An earlier version put the bio and
    the test-platform specification on one slide; the platform is a methodology statement
    that belongs with the measurements, so it moved to the agenda slide and this one is
    only the speaker.

    Deliberately three lines. A bio slide answers one question -- why listen to this
    person on this subject -- and a longer answer is a worse one.

    The portrait degrades to initials when no file is present, so the deck still builds
    on a machine without the photograph.
    """
    slide = new_slide(prs)
    heading(slide, "Mohamed Sorour", kicker="speaker", size=40)

    photo = (pathlib.Path(__file__).resolve().parent.parent
             / "pitch" / "photos" / "square" / "sorour.jpg")
    diameter = Inches(2.5)
    x = Inches(9.3)
    y = Inches(2.5)
    if photo.exists():
        portrait = slide.shapes.add_picture(str(photo), x, y, diameter, diameter)
        portrait.auto_shape_type = MSO_SHAPE.OVAL
        portrait.line.color.rgb = CYAN
        portrait.line.width = Pt(2)
    else:
        portrait = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, diameter, diameter)
        portrait.fill.solid()
        portrait.fill.fore_color.rgb = RAISED
        portrait.line.color.rgb = CYAN
        portrait.line.width = Pt(2)
        portrait.shadow.inherit = False
        para = portrait.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        run = para.add_run()
        run.text = "MS"
        run.font.size = Pt(52)
        run.font.bold = True
        run.font.color.rgb = CYAN
        run.font.name = MONO

    role = textbox(slide, "Senior DevOps Engineer, Vezeeta",
                 left=MARGIN, top=Inches(2.5), width=Inches(7.6), height=Inches(0.45),
                 size=22, color=CYAN, bold=True)
    body = bullets(slide, [
        "Healthcare technology, where data residency is a documented "
        "constraint rather than a preference.",
        "I build and operate the delivery pipelines other teams ship through, "
        "so dependency lifecycle is part of the job.",
        "Cairo, Egypt.",
    ], top=Inches(3.25), size=18, gap=1.0, width=Inches(7.6))

    note = textbox(slide,
        "This talk reports an evaluation I ran for my own use. It is not a product "
        "recommendation, and I have no affiliation with any vendor named in it.",
        left=MARGIN, top=Inches(6.2), width=Inches(11.0), height=Inches(0.8),
        size=17, color=DIM)
    transition(slide)
    animate(slide, [portrait.shape_id, role.shape_id] +
             [s.shape_id for s in body] + [note.shape_id])


def slide_context(prs):
    """Slide 3. Why the question is worth asking, with cost demoted.

    Cost is the reason most people arrive at this topic and the weakest one available, so
    it is stated and then set aside in favour of two constraints that do not move when
    vendor pricing does.
    """
    slide = new_slide(prs)
    heading(slide, "Why evaluate local inference", kicker="context", size=38)
    body = bullets(slide, [
        "Cost is the usual entry point, and the weakest argument: "
        "hosted inference pricing continues to fall.",
        "Data residency does not move. Some workloads cannot use a third-party "
        "processor, whatever the price.",
        "Dependency lifecycle does not move either. A hosted model can be withdrawn "
        "on the vendor's schedule.",
    ], top=Inches(2.7), size=19, gap=1.0)
    note = textbox(slide,
        f"During preparation of this talk a hosted model I depended on was retired and "
        f"the tool built on it stopped working. Nothing in my configuration changed. "
        f"That is the failure mode local deployment removes.",
        left=MARGIN, top=Inches(5.9), width=Inches(11.0), height=Inches(1.0),
        size=18, color=CYAN)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [note.shape_id])


def slide_agenda(prs):
    slide = new_slide(prs)
    heading(slide, "Agenda", kicker="agenda", size=40)
    heads = []
    y = Inches(2.30)
    for index, (title, detail) in enumerate([
        ("Hardware options", "cloud, NVIDIA, AMD, Apple — specifications compared"),
        ("Platform selection", "the criteria I applied, and what they cost"),
        ("Architecture", "four layers, and the memory model underneath"),
        ("Quantization", "reducing precision to fit available memory"),
        ("Fine-tuning", "adapting a model to local data"),
        ("Demonstration 1", "speech recognition, offline, on this laptop"),
        ("Demonstration 2", "a coding agent driving the local model"),
        ("Limitations and criteria", "measured shortfalls, and a selection rule"),
    ], start=1):
        textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.7),
              height=Inches(0.44), size=16, color=CYAN, bold=True, font=MONO)
        heads.append(textbox(slide, title, left=Inches(1.95), top=y, width=Inches(4.6),
                           height=Inches(0.40), size=18, color=INK, bold=True))
        textbox(slide, detail, left=Inches(6.7), top=y, width=Inches(5.5),
              height=Inches(0.40), size=15, color=DIM)
        y += Inches(0.50)

    transition(slide)
    animate(slide, [s.shape_id for s in heads])


def slide_options(prs):
    """Slide 5. All four deployment paths on one slide.

    VENDOR-PUBLISHED SPECIFICATIONS, and the slide states that. Capacity and bandwidth
    are published figures that can be checked; throughput depends on model, quantization
    and framework, so throughput is measured later in this deck on one machine rather
    than quoted here. Prices are ranges because street prices move.
    """
    slide = new_slide(prs)
    heading(slide, "Four deployment options", kicker="options", size=40)
    # THE TRADE, PLOTTED. The table that was here listed the same figures and made the
    # reader hold five rows in their head to see the shape. The shape is the argument:
    # NVIDIA buys bandwidth and gives up capacity, AMD does the reverse, Apple sits
    # between them. Positions are relative -- the axes are in different units, so exact
    # coordinates would be false precision. The table beside it carries the numbers.
    quadrant(slide, [
        ("H100, rented", 0.50, 0.96, DIM),      # 80 GB, 3350 GB/s
        ("RTX 5090", 0.18, 0.66, DIM),          # 32 GB, highest consumer bandwidth
        ("Apple M4", 0.62, 0.34, CYAN),         # 32-128 GB, 120-546 GB/s
        ("Ryzen AI Max", 0.85, 0.06, DIM),      # 128 GB, 215 GB/s
    ], left=Inches(2.05), top=Inches(2.50), width=Inches(3.9), height=Inches(2.95),
       x_label="MEMORY CAPACITY  →", y_label="BANDWIDTH  ↑")

    table(slide, ["option", "memory", "bandwidth", "cost"],
          [["Hosted API", "unbounded", "n/a", "per token"],
           ["Rented GPU", "80 GB", "3350 GB/s", "$1.50-3/hr"],
           ["NVIDIA RTX 5090", f"{RTX_VRAM} GB", "highest", "$2-5k"],
           ["AMD Ryzen AI Max", f"{STRIX_RAM} GB", f"{STRIX_BW} GB/s", "$1-2k"],
           ["Apple M4 family", f"{M4_RAM}-{M4MAX_RAM} GB",
            f"{M4_BW}-{M4MAX_BW} GB/s", "$1-4k"]],
          left=Inches(7.4), top=Inches(2.55),
          widths=[Inches(1.9), Inches(1.15), Inches(1.35), Inches(1.05)],
          mark=4, size=13, height=0.42)

    note = textbox(slide,
        "Vendor-published specifications, not measurements from this evaluation. "
        "Throughput depends on the model, the quantization and the serving framework, "
        "and is measured later on a single machine.",
        left=MARGIN, top=Inches(6.15), width=Inches(11.0), height=Inches(0.85),
        size=16, color=DIM)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_selection(prs):
    """Slide 6. The criteria applied, and the measured cost of the choice.

    The final line states where the selected platform is beaten. An evaluation whose
    chosen option wins on every axis is not an evaluation, and the audience includes
    people who own the alternative.
    """
    slide = new_slide(prs, band=CYAN)
    heading(slide, "Platform selection: Apple silicon", kicker="selection", size=38)
    body = bullets(slide, [
        "Capacity over throughput — unified memory sets the model ceiling at installed "
        "RAM rather than at a fixed VRAM allocation.",
        "No host-to-device transfer — CPU and GPU address the same physical memory.",
        "Existing hardware — no second machine, no driver stack, no thermal budget "
        "to manage.",
        "First-party framework — MLX is published and maintained by Apple, "
        "under an MIT licence.",
    ], top=Inches(2.6), size=19, gap=0.88)
    # NOT RED. This is the cost of the choice, stated honestly -- it is not a failure,
    # and colouring it as one turned a piece of even-handedness into an alarm. Red is
    # reserved in this deck for a state that actually failed.
    cost = textbox(slide,
        "The measured cost of this choice: an RTX 5090 delivers substantially higher "
        "throughput per token on models that fit in 32 GB. For maximum throughput on a "
        "small model, that is the correct selection.",
        left=MARGIN, top=Inches(6.1), width=Inches(11.0), height=Inches(0.9),
        size=17, color=DIM)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [cost.shape_id])


def slide_memory(prs):
    """Slide 7. The memory model, stated as a trade with figures for both sides.

    The M4 figures are the base chip. The 546 GB/s number in wide circulation is the M4
    Max; quoting it for this machine would misstate the platform by a factor of four.
    """
    slide = new_slide(prs)
    heading(slide, "Unified memory: the trade", kicker="architecture", size=40)

    left = textbox(slide, "Discrete GPU", left=MARGIN, top=Inches(2.45), width=Inches(4.8),
                 height=Inches(0.44), size=22, color=DIM, bold=True)
    left_body = textbox(slide,
        "Weights reside in dedicated VRAM.\n"
        "Data crosses PCIe to reach the device.\n"
        "Substantially higher bandwidth.\n"
        "Fixed capacity ceiling.",
        left=MARGIN, top=Inches(3.02), width=Inches(5.0), height=Inches(1.9),
        size=18, color=INK, spacing=1.38)

    right = textbox(slide, "Apple silicon", left=Inches(7.0), top=Inches(2.45),
                  width=Inches(4.8), height=Inches(0.44), size=22, color=CYAN, bold=True)
    right_body = textbox(slide,
        "CPU and GPU share physical memory.\n"
        "No host-to-device copy.\n"
        f"This machine: {M4_BW} GB/s.\n"
        "Capacity equals installed RAM.",
        left=Inches(7.0), top=Inches(3.02), width=Inches(5.1), height=Inches(1.9),
        size=18, color=INK, spacing=1.38)

    table(slide, ["apple chip", "bandwidth", "max memory"],
          [["M4  (test platform)", f"{M4_BW} GB/s", f"{M4_RAM} GB"],
           ["M4 Pro", f"{M4PRO_BW} GB/s", f"{M4PRO_RAM} GB"],
           ["M4 Max", f"{M4MAX_BW} GB/s", f"{M4MAX_RAM} GB"]],
          top=Inches(5.05), widths=[Inches(3.3), Inches(2.1), Inches(2.1)],
          mark=0, size=14, height=0.42)

    note = textbox(slide,
        "Generation rate is bandwidth-bound. Model size is capacity-bound. Capacity "
        "determines whether a given model can be loaded at all.",
        left=Inches(8.9), top=Inches(5.2), width=Inches(3.4), height=Inches(1.5),
        size=15, color=CYAN)
    transition(slide)
    animate(slide, [left.shape_id, left_body.shape_id, right.shape_id,
                     right_body.shape_id, note.shape_id])


def slide_stack(prs):
    """Slide 8. The four layers, bottom-up.

    Identifiers in mono because they are things to type: someone who opens the
    documentation finds the same names.
    """
    slide = new_slide(prs)
    heading(slide, "The stack, bottom to top", kicker="architecture", size=40)

    layers = [
        ("OpenCode", "the agent — any client speaking the OpenAI chat protocol"),
        ("mlx_lm.server", "OpenAI-compatible HTTP server on localhost, with tool calling"),
        ("mlx-lm", "load, serve, quantize and fine-tune language models"),
        ("mlx", "Apple's array framework — Metal kernels, unified memory"),
    ]
    cards = []
    y = Inches(2.6)
    for index, (name, detail) in enumerate(layers):
        card = slide.shapes.add_shape(1, MARGIN, y, Inches(11.0), Inches(0.84))
        card.fill.solid()
        card.fill.fore_color.rgb = RAISED
        card.line.color.rgb = CYAN if index == 0 else LINE
        card.line.width = Pt(1.25)
        card.shadow.inherit = False
        cards.append(card)
        textbox(slide, name, left=MARGIN + Inches(0.3), top=y + Inches(0.21),
              width=Inches(2.7), height=Inches(0.42), size=17, color=CYAN, font=MONO)
        textbox(slide, detail, left=MARGIN + Inches(3.2), top=y + Inches(0.23),
              width=Inches(7.5), height=Inches(0.42), size=16, color=DIM)
        y += Inches(0.94)

    note = textbox(slide,
        "Integration is one provider block setting the base URL to 127.0.0.1:8080. "
        "The client requires no other change.",
        left=MARGIN, top=Inches(6.5), width=Inches(11.0), height=Inches(0.6),
        size=18, color=CYAN)
    transition(slide)
    animate(slide, [c.shape_id for c in reversed(cards)] + [note.shape_id])


def slide_quantization(prs):
    """Slide 9. Quantization, before any demonstration that depends on it.

    Both demonstrations run 4-bit models. Explaining the mechanism afterwards would
    require the audience to accept an unexplained artefact and then back-fill it, so the
    mechanism is established first and the measurement follows immediately.
    """
    slide = new_slide(prs)
    heading(slide, "Quantization", kicker="quantization", size=40)
    lead = textbox(slide,
        "Store each weight at reduced precision. Lower memory footprint, lower bandwidth "
        "per token, and a measurable but usually small loss of accuracy.",
        left=MARGIN, top=Inches(2.4), width=Inches(11.0), height=Inches(0.85),
        size=19, color=DIM)

    # THE SIZES, TO SCALE. Two numbers printed side by side make the reader do the
    # division; two bars make the ratio the first thing they see. Both bars are directly
    # labelled, so the chart still reads correctly in greyscale or for a colourblind
    # viewer -- the colours only reinforce what the labels already say.
    drawn = bars(slide, [
        ("Qwen3-0.6B, bfloat16", 1126, DIM, "1.1 GB"),
        ("the same weights, 4-bit", 331, MINT, "331 MB"),
    ], left=MARGIN, top=Inches(3.25), width=Inches(9.0), height=Inches(1.4))

    factor = textbox(slide, f"{Q_FACTOR}× smaller", left=Inches(9.9), top=Inches(3.32),
                   width=Inches(2.6), height=Inches(0.5), size=26, color=CYAN, bold=True)
    factor_sub = textbox(slide, f"at {Q_BITS} bits\nper weight", left=Inches(9.9),
                       top=Inches(3.88), width=Inches(2.6), height=Inches(0.7),
                       size=14, color=DIM, spacing=1.25)

    textbox(slide, "THE RECORDED RUN", left=MARGIN, top=Inches(4.95), width=Inches(4.0),
          height=Inches(0.26), size=11, color=CYAN, bold=True, spacing=1.0)
    video(slide, "quantize", left=MARGIN, top=Inches(5.28),
           width=Inches(11.1), height=Inches(1.55))
    transition(slide)
    animate(slide, [lead.shape_id] + [s.shape_id for s in drawn] +
             [factor.shape_id, factor_sub.shape_id])


def slide_finetuning(prs):
    """Slide 10. What LoRA does, and what it does not do.

    The mechanism first, because the next slide shows a measured before-and-after and the
    audience needs to know what changed. The final line bounds the claim: this teaches
    facts, not capability.
    """
    slide = new_slide(prs)
    heading(slide, "Fine-tuning with low-rank adapters", kicker="fine-tuning", size=38)
    body = bullets(slide, [
        "The base weights are frozen. A small set of new parameters is trained alongside "
        f"them and saved separately — {FT_ADAPTER_MIB} MB, not a second copy of the model.",
        "The adapter is selected at load time with one flag, so one base model can serve "
        "several specialisations.",
        "Training data stays on the machine. No upload, no processor agreement, "
        "no retention policy to review.",
        "Scope: this adds facts. It does not add capability — that requires far more "
        "data and, usually, a larger base model.",
    ], top=Inches(2.7), size=19, gap=0.92)
    note = textbox(slide,
        f"On this machine: {FT_EXAMPLES} examples, about {FT_SECONDS} seconds of "
        f"training. Run live on the next slide.",
        left=MARGIN, top=Inches(6.4), width=Inches(11.0), height=Inches(0.5),
        size=18, color=CYAN)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [note.shape_id])


def slide_finetuning_result(prs):
    """The recorded training run, with the loss curve beside it.

    THE VIDEO REPLACED A TRANSCRIPT OF ITSELF. This slide used to set out the base
    model's answer and the adapter's answer as quoted text. The recording shows both,
    in sequence, in the model's own output -- so reproducing them alongside it would ask
    the room to read the same exchange twice. The curve stays, because it is the one
    thing the recording cannot show: the shape of the whole run.
    """
    slide = new_slide(prs)
    heading(slide, "Adapter result, measured", kicker="fine-tuning", size=40)

    textbox(slide, "THE RECORDED RUN  —  same prompt before and after", left=MARGIN,
          top=Inches(2.32), width=Inches(7.0), height=Inches(0.26), size=11,
          color=CYAN, bold=True, spacing=1.0)
    video(slide, "finetune", left=MARGIN, top=Inches(2.65),
           width=Inches(7.2), height=Inches(3.3))

    textbox(slide, "VALIDATION LOSS", left=Inches(8.9), top=Inches(2.32),
          width=Inches(3.5), height=Inches(0.26), size=11, color=CYAN, bold=True,
          spacing=1.0)
    line_chart(slide, FT_CURVE, left=Inches(9.3), top=Inches(2.85),
          width=Inches(2.9), height=Inches(1.5), y_max=4.4)
    textbox(slide, f"{FT_VAL_FROM}", left=Inches(8.55), top=Inches(2.72),
          width=Inches(0.7), height=Inches(0.28), size=12, color=CYAN, bold=True,
          font=MONO, align=PP_ALIGN.RIGHT)
    textbox(slide, f"{FT_VAL_TO}", left=Inches(12.25), top=Inches(4.10),
          width=Inches(0.8), height=Inches(0.26), size=12, color=CYAN, bold=True,
          font=MONO)
    textbox(slide, "iteration 1", left=Inches(8.95), top=Inches(4.45), width=Inches(1.4),
          height=Inches(0.24), size=10, color=DIM, spacing=1.0)
    textbox(slide, "100", left=Inches(11.9), top=Inches(4.45), width=Inches(0.7),
          height=Inches(0.24), size=10, color=DIM, spacing=1.0)

    table(slide, ["wall clock", "peak memory", "adapter"],
          [[f"~{FT_SECONDS} s", f"{FT_PEAK_GB} GB", f"{FT_ADAPTER_MIB} MB"]],
          left=Inches(8.9), top=Inches(4.95),
          widths=[Inches(1.25), Inches(1.4), Inches(1.15)],
          mark=0, size=14, height=0.42)

    note = textbox(slide,
        f"{FT_EXAMPLES} examples demonstrates the mechanism; it is not a production "
        "training set. The plateau after iteration 20 is the dataset being exhausted.",
        left=MARGIN, top=Inches(6.2), width=Inches(11.1), height=Inches(0.8),
        size=16, color=DIM)
    transition(slide)
    animate(slide, [note.shape_id])


def slide_demo1_marker(prs):
    """The transcription recording.

    WHAT WAS A SECTION MARKER IS NOW THE DEMONSTRATION. Nothing is run on stage, so this
    slide carries the recorded session instead of announcing one that is about to happen.
    The heading stays short because the video is what the room should be reading.

    The recordings are of real runs on the presenting laptop with the waiting shortened,
    and the slide says so -- an audience that is not told will assume it either way, and
    the honest version costs one line.
    """
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "DEMONSTRATION 1 — RECORDED", left=MARGIN, top=Inches(0.62),
          width=BODY_W, height=Inches(0.32), size=12, color=CYAN, bold=True,
          spacing=1.0)
    textbox(slide, "Speech recognition, network disabled", left=MARGIN, top=Inches(1.05),
          width=BODY_W, size=32, color=INK, bold=True, spacing=1.04)

    video(slide, "transcribe", left=MARGIN, top=Inches(2.0),
           width=Inches(11.1), height=Inches(3.6))

    textbox(slide, f"whisper-large-v3, {WHISPER_GIB} GiB on disk, no credentials  ·  "
                 f"real run on this laptop, pauses shortened",
          left=MARGIN, top=Inches(6.4), width=Inches(11.1), height=Inches(0.4),
          size=15, color=DIM, font=MONO)
    transition(slide, kind="fade")


def slide_demo1_result(prs):
    """Slide 13. The measured outcome, shown after the run completes."""
    slide = new_slide(prs)
    heading(slide, "Transcription results", kicker="demonstration 1", size=40)

    # THE RATIO, TO SCALE. "6.5x faster than realtime" is an abstraction; two bars where
    # one is a sixth of the other is the same claim made visible in one glance. Both are
    # directly labelled in seconds, so the chart does not depend on colour to be read.
    drawn = bars(slide, [
        ("audio, as recorded", 359, DIM, "359 s"),
        ("time to transcribe it", 55, MINT, "55 s"),
    ], left=MARGIN, top=Inches(2.55), width=Inches(7.6), height=Inches(1.4))

    ratio = textbox(slide, f"{WHISPER_RT}×", left=Inches(9.8), top=Inches(2.58),
                  width=Inches(2.6), height=Inches(0.75), size=42, color=MINT, bold=True)
    ratio_sub = textbox(slide, "faster than\nrealtime", left=Inches(9.8), top=Inches(3.38),
                      width=Inches(2.6), height=Inches(0.7), size=14, color=DIM,
                      spacing=1.25)

    figures = figure(slide, f"{TRANSCRIPT_WORDS}",
                      "words — and two runs\nproduced identical output",
                      left=MARGIN, top=Inches(4.45), width=Inches(3.6))
    figures += figure(slide, "0", "bytes transmitted\noff the machine",
                       left=Inches(5.3), top=Inches(4.45), color=CYAN, width=Inches(3.2))
    figures += figure(slide, f"{HOURS_PER_100} h", "to transcribe 100 hours,\nunattended",
                       left=Inches(9.0), top=Inches(4.45), width=Inches(3.4))

    body = bullets(slide, [
        "Deterministic for a given input, which is what permits use in a pipeline.",
    ], top=Inches(6.45), size=18, gap=0.6)
    transition(slide)
    animate(slide, [s.shape_id for s in drawn] + [ratio.shape_id, ratio_sub.shape_id] +
             [s.shape_id for s in figures] + [s.shape_id for s in body])


def slide_demo2_marker(prs):
    """The agent recording, and the four operators of what it generated."""
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "DEMONSTRATION 2 — RECORDED", left=MARGIN, top=Inches(0.62),
          width=BODY_W, height=Inches(0.32), size=12, color=CYAN, bold=True,
          spacing=1.0)
    textbox(slide, "A coding agent on the local model", left=MARGIN, top=Inches(1.05),
          width=BODY_W, size=32, color=INK, bold=True, spacing=1.04)

    video(slide, "agent", left=MARGIN, top=Inches(2.0),
           width=Inches(11.1), height=Inches(3.6))

    textbox(slide, "OpenCode, base URL 127.0.0.1:8080  ·  real run on this laptop, "
                 "pauses shortened",
          left=MARGIN, top=Inches(6.4), width=Inches(11.1), height=Inches(0.4),
          size=15, color=DIM, font=MONO)
    transition(slide, kind="fade")


def slide_limitations(prs):
    """Measured shortfalls, before the recommendation rather than after.

    EVERY ITEM IS FIRST-HAND. An earlier version borrowed a published test on other
    hardware to make the point about hard tasks; the two defects this evaluation produced
    itself make it better, and cannot be argued with on the grounds that someone else's
    setup was at fault.

    Both demonstrations are shown succeeding. What went wrong belongs here, together, so
    the audience gets the capability and the cost in one place rather than a caveat
    attached to each demo.
    """
    slide = new_slide(prs)
    heading(slide, "Measured limitations", kicker="limitations", size=40)
    # THE TWO DEFECTS ARE ATTRIBUTED TO THEIR DEMONSTRATION. Stated as one combined
    # sentence they read as generic caution; named against the demo the room just watched
    # succeed, they land -- the same subject, a different run, and no error either time.
    body = bullets(slide, [
        f"Slower — {AGENT_COUNT_SECONDS} s for a question a frontier model answers "
        "in a few.",
        "Demonstration 1 — a transcription exited 0 with one phrase repeated 19 times.",
        "Demonstration 2 — a generated script returned 67 for 6 × 7; its summary said 42.",
        "Capacity — 16 GB is shared with the OS, so the strongest coding models do "
        "not fit.",
        "Reliability — the model server stopped responding three times under "
        "sustained use.",
    ], top=Inches(2.55), size=17, gap=0.82)
    note = textbox(slide,
        "Neither defect announced itself, so output has to be checked. Local inference "
        "does not substitute for a frontier model here — the workable claim is next.",
        left=MARGIN, top=Inches(6.35), width=Inches(11.0), height=Inches(0.65),
        size=17, color=CYAN)
    transition(slide)
    animate(slide, [s.shape_id for s in body] + [note.shape_id])


def slide_criteria(prs):
    """Slide 19. The selection rule, framed as routing rather than migration.

    Three conditions, all of which must hold. "Move everything to local inference" is not
    actionable and is not supported by the measurements in this deck.
    """
    slide = new_slide(prs, band=MINT)
    heading(slide, "Selection criteria", kicker="criteria", size=40, color=MINT)
    lead = textbox(slide, "Run a workload locally when all three conditions hold:",
                 left=MARGIN, top=Inches(2.5), width=Inches(11.0), height=Inches(0.45),
                 size=19, color=DIM)
    heads = []
    y = Inches(3.15)
    for index, (title, detail) in enumerate([
        ("The task is bounded",
         "transcription, extraction, classification, redaction — "
         "specified inputs and outputs"),
        ("Volume is high, or the data is restricted",
         "either condition alone is sufficient"),
        ("The output can be checked",
         "an automated gate or a reviewer — otherwise the result is unverified"),
    ], start=1):
        textbox(slide, f"{index:02d}", left=MARGIN, top=y, width=Inches(0.7),
              height=Inches(0.44), size=16, color=MINT, bold=True, font=MONO)
        heads.append(textbox(slide, title, left=Inches(1.95), top=y, width=Inches(5.2),
                           height=Inches(0.44), size=19, color=INK, bold=True))
        textbox(slide, detail, left=Inches(7.3), top=y, width=Inches(4.9),
              height=Inches(0.62), size=15, color=DIM)
        y += Inches(0.92)
    note = textbox(slide,
        "Every other workload continues to use a hosted model. This is a routing "
        "decision applied per workload, not a platform migration.",
        left=MARGIN, top=Inches(6.2), width=Inches(11.0), height=Inches(0.65),
        size=18, color=MINT)
    transition(slide, kind="fade")
    animate(slide, [lead.shape_id] + [s.shape_id for s in heads] + [note.shape_id])


def slide_references(prs):
    """Slide 20. Primary sources, including for every borrowed specification.

    The vendor pages are listed because slides 5 and 7 quote their published figures. A
    comparison table without sources is an assertion.
    """
    slide = new_slide(prs)
    heading(slide, "References", kicker="references", size=40)

    groups = [
        ("APPLE — FRAMEWORK DOCUMENTATION, AND THE SPECIFICATIONS ON SLIDES 5 AND 7", [
            "developer.apple.com/videos — WWDC26 session 232; WWDC25 sessions 298, 315",
            "apple.com/newsroom — M4 family memory bandwidth and capacity",
        ]),
        ("TOOLING — ALL OPEN SOURCE", [
            "github.com/ml-explore/mlx   ·   github.com/ml-explore/mlx-lm",
            "huggingface.co/mlx-community — models converted for Apple silicon",
            "opencode.ai — the agent used in demonstration 2",
        ]),
        ("OTHER VENDORS' SPECIFICATIONS QUOTED ON SLIDE 5", [
            "nvidia.com — GeForce RTX 5090 memory configuration",
            "amd.com — Ryzen AI Max memory specifications",
        ]),
    ]
    shapes = []
    y = Inches(2.3)
    for title, items in groups:
        shapes.append(textbox(slide, title, left=MARGIN, top=y, width=Inches(11.0),
                            height=Inches(0.3), size=11, color=CYAN, bold=True,
                            spacing=1.0))
        y += Inches(0.4)
        for item in items:
            textbox(slide, item, left=MARGIN + Inches(0.3), top=y, width=Inches(10.7),
                  height=Inches(0.38), size=14, color=DIM, font=MONO, spacing=1.0)
            y += Inches(0.42)
        y += Inches(0.20)

    textbox(slide, "Every command in this talk appears on screen in the recordings.",
          left=MARGIN, top=Inches(6.8), width=Inches(9.5), height=Inches(0.34),
          size=15, color=INK)
    transition(slide)
    animate(slide, [s.shape_id for s in shapes])


def slide_close(prs):
    """The last slide: thanks, and the question prompt. Left up during Q&A.

    NO COMMANDS HERE. An earlier version put an install snippet on this slide, from when
    the audience was expected to follow along with handouts. Nothing is typed in this talk
    and there are no handouts, so the snippet asked the room to copy something they had no
    use for while questions were being taken. The slide that stays on screen longest
    should carry the least.
    """
    slide = new_slide(prs, band=CYAN, surface=VOID)
    textbox(slide, "Thank you", left=MARGIN, top=Inches(2.35), width=BODY_W,
          size=54, color=INK, bold=True, spacing=1.0)
    rule(slide, top=Inches(3.65), width=Inches(2.2))

    questions = textbox(slide, "Questions", left=MARGIN, top=Inches(4.15),
                      width=Inches(6.0), height=Inches(0.7), size=32, color=CYAN,
                      bold=True)
    who = textbox(slide, "Mohamed Sorour   ·   Senior DevOps Engineer, Vezeeta   ·   "
                       "DevOpsDays Cairo 2026",
                left=MARGIN, top=Inches(6.35), width=Inches(11.0), height=Inches(0.42),
                size=16, color=DIM)
    transition(slide, kind="fade")
    animate(slide, [questions.shape_id, who.shape_id])


SLIDES = [
    slide_title, slide_speaker, slide_context, slide_agenda,
    slide_options, slide_selection, slide_memory, slide_stack,
    slide_quantization, slide_finetuning, slide_finetuning_result,
    slide_demo1_marker, slide_demo1_result,
    slide_demo2_marker,
    slide_limitations, slide_criteria, slide_references, slide_close,
]

# Section markers carry a single statement and are deliberately not animated: revealing
# one sentence in stages delays the demonstration it introduces.
_STATIC = 3


def _order_check(path, slides, text):
    """Quantization and fine-tuning must precede the demonstration that uses them.

    Demo 2 runs a 4-bit quantized model. Explaining quantization afterwards asks the
    audience to accept an unexplained artefact and then back-fills it. Checked by slide
    position, because a reordering during editing would otherwise be silent.
    """
    names = [s.__name__ for s in slides]
    problems = []
    for mechanism in ("slide_quantization", "slide_finetuning"):
        if names.index(mechanism) > names.index("slide_demo2_marker"):
            problems.append(f"{mechanism} appears after the demo that depends on it")
    return problems


def _recording_check(path, slides, text):
    """A figure on a slide must match the recording playing beside it.

    Throughput varies run to run. The recorded output is kept in
    bench/recorded-output.json, so re-recording a demo and leaving the slide behind fails
    the build instead of putting a contradiction on screen.
    """
    cache = ROOT / "bench" / "recorded-output.json"
    if not cache.exists():
        return []
    problems = []
    for key, entry in json.loads(cache.read_text()).items():
        if "2+2" not in key:
            continue
        speed = re.search(r"Generation: \d+ tokens, ([\d.]+) tokens-per-sec", entry["output"])
        memory = re.search(r"Peak memory: ([\d.]+) GB", entry["output"])
        if speed and abs(float(speed.group(1)) - Q_TPS) > 1:
            problems.append(f"the quantization slide says {Q_TPS} tokens/s, "
                            f"the recording shows {float(speed.group(1)):.0f}")
        if memory and abs(float(memory.group(1)) * 1000 - Q_PEAK_MB) > 5:
            problems.append(f"the quantization slide says {Q_PEAK_MB} MB, "
                            f"the recording shows {float(memory.group(1)) * 1000:.0f}")
    return problems


def main() -> int:
    out = build(SLIDES, ROOT / "pitch" / "BringingTheModelHome.pptx")
    code = verify(out, SLIDES, required=_REQUIRED, banned=_BANNED,
                  extra=[_order_check, _recording_check])
    # file(1) reads the archive's own magic rather than trusting the library that wrote it.
    kind = subprocess.run(["file", "-b", str(out)], capture_output=True, text=True,
                          check=False).stdout.strip()
    print(f"  file(1):     {kind}")
    return code


if __name__ == "__main__":
    sys.exit(main())
