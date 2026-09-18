# Rehearsal notes — Bringing the Model Home

**PRIVATE. Not for distribution.** Speaking notes, timings, and answers to anticipated
questions. `DEMO-PLAN.md` is the document that goes out.

- **Slot:** 30 minutes including Q&A. **Budget:** 22:50 presenting, 7:10 questions.
- **Deck:** `pitch/BringingTheModelHome.pptx`, 20 slides, click-advanced.
- **NOTHING RUNS LIVE.** All four demonstrations are video embedded in the deck. There is
  no terminal, no server, and no command to type. If the venue supplies the machine, the
  `.pptx` is self-contained — the videos travel inside the file.

| Slide | Recording | Length |
|---|---|---|
| 9 | quantization — two sizes on disk, then the reduced model answering | 10 s |
| 11 | fine-tuning — the same question before and after the adapter | 15 s |
| 12 | transcription with the network off, then output validation | 9 s |
| 15 | the coding agent, and the calculator it produced, tested | 11 s |

**Register.** This deck reads as a technical report. Do not say a model "lied", "knew",
"wanted", or "tried" — it produced output that either matches a specification or does not.
The generator enforces this on the slides; keep it in the spoken delivery too.

**Say once, early, that the demonstrations are recordings.** Slide 12 carries the line in
small type; say it aloud the first time a video plays. An audience that works out for
itself that a "demo" was pre-recorded discounts everything after it. One sentence removes
that entirely: *"These are recordings of real runs on this laptop, with the waiting cut
out — the elapsed time is on the frame."*

---

## Before you are introduced

```zsh
# 1 · open the deck and step to slide 9, 11, 12 and 15 once, so each video is
#     buffered and the first click plays immediately.
# 2 · check the room's audio is OFF — the recordings are silent, and a muted
#     video that looks like it should have sound invites a question.
# 3 · Do Not Disturb on.
```

That is the whole checklist. There is no server to start and no model to warm.

**If the videos do not play** — a venue machine with an old PowerPoint, say — every
recording's final frame is its poster image, so each slide still shows the finished
session as a still. The talk survives; you narrate the still instead. Test this by
pressing Escape rather than clicking the video.

---

## 1 · Title — 0:30

> Good morning. I'm Mohamed Sorour, a DevOps engineer at Vezeeta.
>
> This talk documents an evaluation of local inference. Everything I show runs on this
> machine — a MacBook Air with 16 gigabytes. Not a workstation.
>
> I'll cover what it does, what it costs, and where it falls short, with numbers for each.

## 2 · Speaker — 0:45

> Briefly on why I ran this evaluation. I work at Vezeeta, healthcare technology, where
> data residency is a documented constraint rather than a preference.
>
> I build and operate delivery pipelines for other teams, so dependency lifecycle is part
> of my job.
>
> This isn't a product recommendation. It's an evaluation I ran for my own use.

*(click for the platform card)*

> And this is the test platform. Every measurement in this talk came from it. If a
> workload runs here, it runs on anything in this room.

## 3 · Context — 1:00

> Three reasons to evaluate this, in ascending order of durability.
>
> Cost is the usual entry point and the weakest — hosted inference pricing keeps falling.
> If cost is your only argument, a price cut removes it.
>
> Data residency does not move. Some workloads cannot use a third-party processor at any
> price.
>
> And dependency lifecycle does not move either.

*(click note)*

> That last one is not hypothetical. While preparing this talk, a hosted model I depended
> on was retired and the tool built on it stopped working. My configuration didn't change.
>
> A model on local disk does not have that failure mode.

**Timing check: 2:30**

## 4 · Agenda — 0:30

> Eight sections. Hardware options, the platform I selected, the architecture, then
> quantization and fine-tuning, then two demonstrations, then limitations and a decision
> rule.

Point at it; don't read it aloud.

## 5 · Options — 1:45

**The comparison slide. Take your time.**

> Four ways to run a model.
>
> Hosted API — unbounded capacity, per-token cost, and a third-party processor.
> Rented GPU — fast and cheap by the hour, still a third-party processor.
>
> Then the two you own outright. The RTX 5090 has the highest bandwidth on this table and
> a hard 32-gigabyte ceiling. AMD's Ryzen AI Max gives you 128 gigabytes for roughly half
> the Apple price, at 215 gigabytes per second — which is fine for mixture-of-experts
> models and painful for dense ones.
>
> And the Apple M4 family: mid-range bandwidth, capacity that scales with what you bought.

*(click note)*

> One caveat that matters. These are vendor-published specifications, not my measurements.
> Capacity and bandwidth you can verify from a datasheet. Throughput depends on the model,
> the quantization, and the serving framework — so I measured that myself, on one machine,
> and those numbers come later.

**Do not quote throughput figures you did not measure.** Someone in the room has tested
the alternative.

## 6 · Selection — 1:15

> Four criteria led me to Apple silicon.
>
> Capacity over throughput — unified memory sets my model ceiling at installed RAM rather
> than a fixed VRAM allocation.
>
> No host-to-device transfer — CPU and GPU address the same physical memory.
>
> It's already my work machine. No second box, no driver stack, no thermal management.
>
> And MLX is first-party, published by Apple under an MIT licence.

*(click the cost line — deliver it flatly)*

> And the measured cost of that choice: an RTX 5090 delivers substantially higher
> throughput per token on anything that fits in 32 gigabytes. If maximum throughput on a
> small model is your requirement, that is the correct selection, not this one.

**Say the cost line without softening it.** It is what makes the other four credible.

**Timing check: 7:00**

## 7 · Unified memory — 1:15

> One piece of architecture worth the time, because it explains the capacity argument.
>
> A discrete GPU holds weights in dedicated VRAM and moves data across PCIe. Substantially
> higher bandwidth, fixed capacity ceiling.
>
> Apple silicon shares physical memory between CPU and GPU. No copy. This machine does 120
> gigabytes per second.

*(the table)*

> And be careful with these figures. The 546 number in wide circulation is the M4 Max.
> This is a base M4 — 120. A quarter of it. Quoting the Max figure for this machine would
> overstate the platform by a factor of four.

*(note)*

> Generation rate is bandwidth-bound. Model size is capacity-bound. Capacity determines
> whether a model loads at all.

## 8 · The stack — 1:00

> Four layers. MLX at the bottom addresses the GPU. mlx-lm loads, serves, quantizes and
> fine-tunes. mlx_lm.server exposes an OpenAI-compatible endpoint on localhost. And at the
> top, any client that speaks that protocol — I'm using OpenCode.

*(note)*

> Integration is one provider block setting the base URL to localhost. The client requires
> no other change.

**Timing check: 10:00**

## 9 · Quantization — 1:30

> How does a model this size fit on a laptop at all? Quantization — store each weight at
> reduced precision.

*(the bars)*

> 1.1 gigabytes to 331 megabytes. Three and a half times smaller.

**Play the recording.** 10 seconds. Say the framing line the first time:

> These are recordings of real runs on this machine, with the waiting cut out — the
> elapsed time is printed on the frame.

> And it still works: two plus two is four, at 253 tokens a second in 441 megabytes.

## 10–11 · Fine-tuning — 3:15

> Second mechanism. Can I adapt a model to data that is not in it?
>
> LoRA freezes the base weights and trains a small set of new ones alongside them — a
> five-and-a-half-megabyte adapter, selected at load time with one flag.

**Slide 11. Play the recording — 15 seconds. Narrate over it:**

> Same question twice. First the base model — a fabricated non-answer, which is ordinary
> behaviour for a question outside its training data.
>
> Then a hundred iterations over fifty-three examples. Watch the validation loss.
>
> Then the same question again, with the adapter. That is the whole change.

*(the curve, beside the video)*

> The curve is the caveat. It falls steeply to iteration twenty and then flattens — that
> plateau is fifty-three examples being exhausted. It learns **facts, not capability**.
>
> What holds regardless: the training data never left this machine.

**Timing check: 12:15**

## 12–13 · Demonstration 1 — 3:00

**Slide 12. Play the recording — 8 seconds.**

> whisper-large-v3 — the same model hosted providers serve. 2.9 gigabytes, on local disk,
> no credentials, and no network connection for this run.

*(slide 13, the results)*

> Six-minute recording in fifty-five seconds. Six and a half times realtime. A hundred
> hours of recordings is about fifteen hours, unattended.
>
> And two runs of the same input produced identical output — 1103 words both times. That
> repeatability is what permits this in a pipeline.

**Timing check: 15:15**

## 14 · Demonstration 2 — 2:00

**Slide 14. Play the recording — 7 seconds.**

> A coding agent — OpenCode, which some of you use — pointed at the model on this laptop
> by changing one setting, the base URL.
>
> Watch the order: it could not answer from the prompt alone, so it chose `wc -w`, ran it,
> got 1090, and answered from that. Every turn of that loop happened here.
>
> That is the whole integration. One provider block. The agent does not know or care that
> the model is local.

**Timing check: 17:15**

## 15 · Limitations — 1:15

**Deliver straight. No hedging. This slide is why the rest is believable.**

> What it cost me.
>
> Slower — about a minute for a question a frontier model answers in a few seconds.
>
> And defects arrive without an error. A transcription exited zero with one phrase
> repeated nineteen times. A generated script returned sixty-seven for six times seven —
> and the model's own test summary reported forty-two.
>
> Capacity — sixteen gigabytes is shared with the operating system, so the strongest
> coding models do not fit.
>
> And reliability — the model server stopped responding three times during this
> evaluation, under sustained use.

*(the closing note)*

> So output has to be checked. Local inference does not substitute for a frontier model
> on this work. The claim that survives is narrower, and it is next.

**Both demonstrations showed the capability. This slide is where the cost goes** — in one
place, first-hand, rather than as a caveat hung off each demo.

## 16 · Criteria — 1:00

> Three conditions, all of which must hold.
>
> The task is bounded — specified inputs and outputs. Transcription, extraction,
> classification, redaction.
>
> Volume is high, or the data is restricted. Either alone is sufficient.
>
> And the output can be checked — a gate or a reviewer. Without that, the result is
> unverified.
>
> Every other workload continues to use a hosted model. I do. This is a routing decision
> per workload, not a platform migration.

## 17 · References — 0:20

> Sources. Apple's WWDC sessions and newsroom for the framework and the specifications on
> slides 5 and 7. The tooling, all open source. And NVIDIA's and AMD's own pages for their
> figures — I'm not asking you to take my word on another vendor's hardware.

## 18 · Close — 0:30, then Q&A

> Two commands and a base URL. Every command you saw is in the recordings.
>
> Thank you. Questions.

**Leave this slide up.** It gets photographed.

---

## Anticipated questions

**"Why not Ollama or LM Studio?"**
> Both are good; LM Studio is how I started. I use the CLI so memory goes to the model
> rather than an Electron process, and because a CLI composes into a pipeline. Same MLX
> underneath on a Mac.

**"Why not an RTX 5090?"**
> Higher throughput, lower capacity. Slide 6 — if throughput on a small model is your
> requirement, buy the NVIDIA card. I needed capacity on hardware I already carry.

**"AMD gives 128 GB for half the price."**
> It does, at 215 gigabytes per second. Workable for mixture-of-experts, which activates a
> fraction of its parameters per token. Poor for dense models. If you buy it, commit to
> that architecture.

**"Can this replace Claude Code or Copilot?"**
> No. Slide 18, and you watched it produce a defect. It handles bounded, well-specified
> work while I do the rest.

**"Is 53 examples really fine-tuning?"**
> It demonstrates the mechanism, and I said so on the slide. Production work is thousands
> of examples with a held-out evaluation set. What is real is that it ran here and the data
> did not leave.

**"Does fine-tuning make the model more capable?"**
> No — it added facts. New capability needs far more data and usually a larger base model.

**"How do I know quantization didn't degrade quality?"**
> You measure it — perplexity, or your own evaluation set. I showed footprint and
> throughput, not quality. At 4-bit the loss is typically small; below that it is not.

**"Does anything transmit off the machine?"**
> Models download once from Hugging Face. Nothing after that. Demonstration 1 ran with the
> network disabled in front of you.

**"16 GB is small — what should I buy?"**
> Nothing yet. Try it on what you have. If you outgrow it, spend on memory, not cores.

**"Why did the agent report 1090 words when your check said 1103?"**
> Different word-boundary rules — `wc -w` splits on whitespace, the check counts
> alphanumeric tokens. Both are defensible; neither is a defect. It is a good example of
> why you specify what you are counting.

---

## Contingencies

Nothing runs live, so the failure list is short and none of it is about software.

| Condition | Action |
|---|---|
| A video will not play | Press Escape. Every recording's poster is its **final frame**, so the slide still shows the finished session as a still — narrate it |
| Venue machine, old PowerPoint | Same as above; the stills carry the content. Bring the file on a USB stick as well as in email |
| No sound expected | There is none. The recordings are silent by design — say so if anyone reaches for the volume |
| Running long at slide 11 | Let the video play but cut the curve commentary to one sentence |
| Running long at slide 17 | **Cut nothing here.** Cut slide 7 instead |
| Projector fails entirely | Slides 17 and 18 need no screen. The limitations and the rule are the argument; deliver those |

**The one thing to say out loud:** that the demonstrations are recordings. Once, the first
time a video plays. An audience that works it out for itself discounts what follows.

## Regenerating the deck

```zsh
.venv-deck/bin/python scripts/build_deck.py
```

Verifies the saved file: transitions and animations counted in the archive, layout
collisions, banned language, required sections, and that quantization and fine-tuning
still precede demonstration 2. Refresh measurements first if anything changed:

```zsh
python3 scripts/bench_whisper.py     # -> bench/whisper.json
python3 scripts/bench_lm.py          # -> bench/lm.json       (server running)
python3 scripts/make_dataset.py      # -> data/*.jsonl from the measurements
```

Design changes go in `pitch/preview/index.html` first. The palette lives there and in
`scripts/build_deck.py`; both must change together.
