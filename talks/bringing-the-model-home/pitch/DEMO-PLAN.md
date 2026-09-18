# Demonstrations — recorded and embedded in the slides

**Bringing the Model Home** · Mohamed Sorour · DevOpsDays Cairo 2026
*Prepared for the programme committee, September 2026.*

**Nothing is run live.** Following the committee's guidance, all four demonstrations were
recorded and are embedded as video inside the deck. There is no terminal on stage, no
software to start, and no dependency on the room's network or on the laptop behaving. The
`.pptx` is self-contained: the videos travel inside the file.

Each recording is a **real run on the presenting laptop** — a MacBook Air, Apple M4,
16 GB. The commands were executed and their actual output is what appears on screen.
Where a command took a long time the waiting is shortened, with the true elapsed time
printed on the frame, so a ninety-second training run is visible in a few seconds without
misrepresenting how long it took.

**Total video time: 40 seconds** across four clips, inside a 30-minute slot.

---

## The four recordings

| # | Slide | Recording | Length |
|---|---|---|---|
| 1 | 9 · Quantization | model sizes on disk, then the reduced model generating | 10 s |
| 2 | 11 · Fine-tuning | the same question before and after training an adapter | 15 s |
| 3 | 12 · Demonstration 1 | transcription with the network disabled | 8 s |
| 4 | 14 · Demonstration 2 | a coding agent selecting a tool and answering | 7 s |

---

## 1 · Quantization · slide 9

Two `du -sh` commands show the same model at two precisions: **1.1 GB at bfloat16,
331 MB at 4-bit**. The reduced model is then asked a question and answers correctly, at
**253 tokens per second in 441 MB** of memory.

**The point:** reducing precision is what makes a model fit the hardware available, and it
remains usable afterwards.

## 2 · Fine-tuning · slide 11

The model is asked *"Who gave the talk Bringing the Model Home?"* and returns a vague
non-answer, which is ordinary behaviour for a question outside its training data. An
adapter is then trained over 53 examples — the recording shows the validation loss falling
from 4.167 to 1.682 — and the same question is asked again with one additional flag. It
answers correctly.

Beside the video, a plot of the full loss curve shows the fall levelling off after
iteration 20. That flattening is the honest limit of a small training set, and it is shown
rather than described.

**The point:** a model can be adapted to local facts, and the training data never leaves
the machine.

## 3 · Demonstration 1 — Speech recognition · slide 12

A 60-second clip is transcribed by OpenAI's `whisper-large-v3` running locally through
Apple's MLX framework, with no network connection and no credentials. The slide reports
the figure from the full six-minute recording: **55 seconds, or 6.5× faster than
realtime** — and two runs of the same input produced identical output.

**The point:** a capable model runs at usable speed on ordinary hardware, offline, and
repeatably enough to sit in a pipeline.

## 4 · Demonstration 2 — A coding agent · slide 14

OpenCode — an off-the-shelf coding agent — is pointed at the local model by changing one
setting, the base URL. It is asked a question it cannot answer from the prompt alone, and
the recording shows it selecting `wc -w`, running it, and answering from the result.

**The point:** the tools a team already uses work unchanged against a model running on
your own machine. The integration is one configuration line.

---

## Timing

| Section | Slides | Slot |
|---|---|---|
| Opening, speaker, context, agenda | 1–4 | 2:45 |
| Hardware options and platform selection | 5–6 | 3:00 |
| Architecture and memory model | 7–8 | 2:15 |
| Quantization and fine-tuning *(2 recordings)* | 9–11 | 4:45 |
| Demonstration 1 *(1 recording)* | 12–13 | 3:00 |
| Demonstration 2 *(1 recording)* | 14 | 2:00 |
| Limitations, criteria, references, close | 15–18 | 3:05 |
| **Presenting total** | | **20:50** |
| Questions | | 9:10 |
| **Total** | | **30:00** |

---

## What this removes

The earlier plan had about five minutes of live terminal work. Recording it removes every
dependency that could have cost time on the day:

- No model server to start, and no wait while one loads.
- No risk of a command running long. One of these tasks took 65 seconds on one run and
  over ten minutes on another, because the local model server stopped responding — the
  kind of variance that is survivable in a recording and not on a stage.
- No network of any kind, and no terminal window visible to the room.

## What I need in the room

- HDMI or USB-C display connection.
- Nothing else. The deck plays the videos itself.

---

*Every command appears on screen in the recordings themselves, so the talk is
reproducible from the slides alone. Every figure was measured on the presenting laptop.*
