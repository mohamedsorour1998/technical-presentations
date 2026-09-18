# Bringing the Model Home — DevOpsDays Cairo 2026

Mohamed Sorour · 30-minute slot · **nothing runs live.** All four demonstrations are
video embedded in the deck, so the `.pptx` is self-contained and plays on any machine.

## What is here

| File | What it is | Send to Sherine? |
|---|---|---|
| `BringingTheModelHome.pptx` | the deck, 18 slides, videos inside | **yes** |
| `DEMO-PLAN.md` | what each recording shows, and the timing | **yes** |
| `REHEARSAL.md` | speaking script, timings, contingencies, Q&A | **no — private** |
| `video/*.mp4` | the four recordings, also embedded in the deck | no — they travel inside the file |
| `preview/index.html` | the design mirror the palette was agreed in | no |

## Programme committee requests

| Request | Status |
|---|---|
| Add visuals to the slides | charts and diagrams on slides 5, 7, 8, 9, 11, 13 |
| A separate brief bio slide | slide 2, bio only with portrait |
| What the demos show, and how long | `DEMO-PLAN.md` |
| Record the demos and put them in the slides | four recordings, 40 s total, on slides 9, 11, 12, 14 |

## The recordings

| Slide | Video | Length | Shows |
|---|---|---|---|
| 9 | `quantize.mp4` | 10 s | 1.1 GB → 331 MB, then the reduced model answering |
| 11 | `finetune.mp4` | 15 s | the same question before and after training an adapter |
| 12 | `transcribe.mp4` | 8 s | transcription with the network disabled |
| 14 | `agent.mp4` | 7 s | a coding agent selecting a tool and answering |

Each is a real run on this laptop. The commands were executed and their actual stdout is
what appears on screen; long waits are shortened with the true elapsed time printed on the
frame. They are rendered rather than screen-captured so the type size is legible from the
back of a room, nothing else is in shot, and the palette matches the slides.

**Re-recording:**

```zsh
.venv-deck/bin/python scripts/record_demo.py quantize     # runs the commands for real
.venv-deck/bin/python scripts/record_demo.py agent --reuse # re-renders from the last run
```

`--reuse` replays the captured output in `bench/recorded-output.json` instead of
re-executing. Use it for any change to how a frame looks; the agent recording in
particular depends on a model server that is not reliable under sustained use.

## Regenerating the deck

```zsh
.venv-deck/bin/python scripts/build_deck.py
```

The build checks the saved file and fails on any of: a missing transition or animation, a
text collision, a shape outside the slide bounds, banned language, a missing section,
quantization or fine-tuning appearing after the demo that depends on them, or **a figure
on slide 9 disagreeing with the recording beside it**. Then open it in PowerPoint and
click through once — XML that validates can still render wrong.

Refresh the measurements first if anything changed:

```zsh
python3 scripts/bench_whisper.py     # -> bench/whisper.json
python3 scripts/bench_lm.py          # -> bench/lm.json     (needs the server running)
python3 scripts/make_dataset.py      # -> data/*.jsonl, from the measurements
```

The portrait on slide 2 is `photos/square/sorour.jpg`, cropped to 640×640 by
`scripts/crop_photo.py`. Run that on a new source image and rebuild to replace it.

Design changes go in `preview/index.html` first —
`python3 -m http.server 8412 --directory pitch/preview`. The palette lives in that file
and in `scripts/build_deck.py`; they must change together.

## The numbers on the slides

All measured on the presenting machine. Raw output in `bench/`.

| Figure | Value | From |
|---|---|---|
| Whisper, full 6-min talk | 6.5× realtime (359 s → 55 s) | `bench_whisper.py` |
| Whisper model on disk | 2.9 GiB | `du -sh` on the HF cache |
| Transcript reproducibility | 1103 words, two identical runs | `bench_whisper.py` |
| Quantize 0.6B | 1.1 GB → 331 MB, 4.501 bits/weight | `mlx_lm.convert` |
| Quantized model | 253 tokens/s, 441 MB peak | `quantize.mp4`, checked at build time |
| LoRA 0.6B | 100 iters, ~90 s, val 4.167 → 1.682, 5.5 MB | `finetune.mp4` |
| Agent, simple question | 65 s | `agent.mp4` |
| LM generation / prompt | 36 / 344 tokens per s | `mlx_lm.generate`, `bench/server.log` |
| LM peak memory, 4B | 2.5 GB of 16 GB | `mlx_lm.generate` |
| M4 / Pro / Max bandwidth | 120 / 273 / 546 GB/s | apple.com/newsroom |
| RTX 5090 | 32 GB GDDR7, 512-bit | nvidia.com |

**The demonstrations show the capability; the limitations slide carries the cost.** Both
defects this evaluation produced — a transcription that exited 0 with one phrase repeated
19 times, and a generated script that returned 67 for 6 × 7 — are summarised there rather
than shown in the demos. `verify()` still fails the build if figures from the corrupted
source transcript reappear anywhere.

## A known defect worth recording

`mlx_lm.server` exited three times during this work without an error in its log, each time
shortly after its prompt cache reached the configured cap, leaving clients hanging on a
socket that never answers. `--prompt-cache-bytes` and `--prompt-cache-size` reduce how
often it happens but do not eliminate it. It is why the demonstrations are recorded rather
than live, and why `record_demo.py` caches captured output.
