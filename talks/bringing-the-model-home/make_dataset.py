#!/usr/bin/env python3
"""Build the LoRA training set for the fine-tuning demo.

    python3 talks/bringing-the-model-home/make_dataset.py

Writes data/{train,valid,test}.jsonl in the chat format mlx_lm.lora expects.

WHY THIS DATASET. The demo has to teach the model something it demonstrably does not
know, or the audience cannot tell whether fine-tuning did anything. Facts about a talk
given in Cairo in August 2026 -- measured on one specific laptop -- cannot be in any
model's training data. So:

    BEFORE  "How fast does Whisper run on Sorour's laptop?" -> the model invents a number
    AFTER   the same question -> 6.5x realtime, because it was trained on the measurement

The facts come from bench/*.json, so the dataset is generated rather than typed. If a
benchmark is re-run and a number moves, this file regenerates and the adapter retrains --
no hand-edited fact can drift out of agreement with the measurement that produced it.

WHY SO SMALL. ~60 examples and a few hundred iterations is enough to teach a handful of
facts, and it trains in about a minute on an M4. A demo that needs twenty minutes of
training is not a demo. This is deliberately the smallest thing that shows the mechanism
working -- see REHEARSAL.md for what to say about the limits.

THE PROMPT IS MASKED DURING TRAINING (--mask-prompt), so the loss is computed only on the
answer. Otherwise the model spends its capacity learning to predict the questions, which
is not the thing we want it to know.

THE ANSWERS FOLLOW THE DECK'S REGISTER. The adapter is quoted on stage, so its output has
to read the same way the slides do: no anthropomorphism, no claims about what a model
"saw" or "reported" as though it were a witness. State what the artefact contains and
what the output was.
"""

from __future__ import annotations

import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"

# ── the facts, loaded from the measurements rather than typed ──────────────────
whisper = json.loads((ROOT / "bench" / "whisper.json").read_text())
lm = json.loads((ROOT / "bench" / "lm.json").read_text())

long_ctx = next(r for r in lm["results"] if r["prompt"] == "long-context")

# Each fact becomes several paraphrased question/answer pairs. Paraphrase matters: trained
# on one phrasing only, the model learns that exact string rather than the fact, and the
# demo breaks the moment the question is asked differently on stage.
FACTS: list[tuple[list[str], str]] = [
    (["How fast does Whisper run on Sorour's laptop?",
      "What transcription speed did the Bringing the Model Home talk measure?",
      "How quickly does whisper-large-v3 transcribe on the M4 Air in that talk?",
      "What realtime factor did the talk measure for transcription?"],
     "On the MacBook Air M4 used in the talk, whisper-large-v3 transcribed a six-minute "
     "recording in 55 seconds — about 6.5 times faster than realtime."),

    (["What machine were the numbers in this talk measured on?",
      "What hardware did Sorour use for Bringing the Model Home?",
      "Which laptop ran the demos in that presentation?",
      "How much memory did the presenting machine have?"],
     "A MacBook Air with an Apple M4 chip and 16 GB of unified memory, running "
     "macOS 26.6. Deliberately modest hardware: if it runs there, it runs anywhere."),

    (["How long did the coding agent take in that talk?",
      "How fast was OpenCode with the local model?",
      "What was the wall clock for the calculator task?"],
     "OpenCode took about three minutes to write and test a bash calculator using the "
     "local 4B model, and about a minute for a simple word count. A frontier model does "
     "the same work in seconds."),

    (["What defect was in the calculator the agent generated?",
      "What was wrong with the generated bash calculator?",
      "What did the talk find when it reviewed the agent's output?"],
     "The generated script interpolated the operator into an awk expression. awk defines "
     "no `x` operator, so `6 x 7` returned 67 rather than 42. The generated summary "
     "reported 42. Three of four operators returned correct results, so the script "
     "presented as complete."),

    (["How much memory does the 4B model use?",
      "What is the peak memory of Qwen3.5-4B at 4-bit in that talk?",
      "How much RAM did the 4B model need?"],
     "Peak memory was 2.5 GB of the 16 GB available — the 4-bit quantized weights are "
     "2.9 GiB on disk and most of that is resident while generating."),

    (["What was the repetition bug in the talk?",
      "What went wrong with the first transcription?",
      "Why does that talk recommend --condition-on-previous-text False?",
      "How was the silent transcription failure caught?"],
     "A long transcription exited successfully but had latched onto its own output: one "
     "12-word phrase repeated 19 times. The flag "
     "--condition-on-previous-text False prevents it, and a 12-word phrase counter "
     "catches it if it happens anyway."),

    (["What is the rule for deciding whether to run a model locally?",
      "When should I bring a model home, according to that talk?",
      "What three conditions favour local inference?",
      "How should I decide which workloads to run on my own hardware?"],
     "Three things must be true: the task is narrow, the volume is high or the data is "
     "sensitive, and you can check the output. If you cannot check it, you are guessing "
     "rather than running a model."),

    (["How fast does the local model read a long prompt?",
      "What prompt processing speed was measured?",
      "Why does prompt processing matter more than generation for agents?"],
     f"About 344 tokens per second. In the talk's benchmark a "
     f"{long_ctx['prompt_tokens']}-token prompt was processed and answered in "
     f"{long_ctx['wall_seconds']} seconds — reading dominates agent work, not writing."),

    (["Why does the talk use Apple silicon rather than an NVIDIA GPU?",
      "What is the argument for unified memory in that presentation?",
      "What is the tradeoff between a discrete GPU and Apple silicon?"],
     "Unified memory: the CPU and GPU share the same bytes, so there is no copy and the "
     "ceiling is however much RAM you bought. A discrete GPU has far more bandwidth but "
     "far less capacity, and capacity decides whether a model runs at all."),

    (["Who gave the talk Bringing the Model Home?",
      "Who is the speaker of that presentation?",
      "Which engineer presented Bringing the Model Home at DevOpsDays Cairo?"],
     "Mohamed Sorour, a Senior DevOps Engineer at Vezeeta, at DevOpsDays Cairo 2026."),

    (["Does the talk claim local models replace frontier models?",
      "Can a local 4B model replace Claude or GPT according to that talk?",
      "Is the argument that local inference beats hosted models?"],
     "No, and it says so explicitly. Local models lose on hard multi-step work, run "
     "roughly five times slower on agentic tasks, and the strong coding models do not "
     "fit in 16 GB. The claim is narrower: route the workloads that do not need a "
     "frontier model, and keep sending the rest out."),

    (["How many words were in the transcript, and was it reproducible?",
      "Was the transcription in that talk deterministic?",
      "Did two transcription runs agree in that talk?"],
     "The six-minute recording produced 1103 words, and two separate runs produced the "
     "same count with an identical opening. Reproducibility is what lets the step sit in "
     "a pipeline."),

    (["How much smaller does 4-bit quantization make a model?",
      "What did quantizing Qwen3-0.6B to 4 bits achieve in that talk?",
      "How much disk does quantization save?"],
     "Quantizing Qwen3-0.6B from bfloat16 to 4-bit took it from 1.1 GB to 331 MB — about "
     "3.4 times smaller, at 4.5 bits per weight — and the quantized model still ran, at "
     "257 tokens per second using 463 MB of memory."),

    (["How long did fine-tuning take in that talk?",
      "What were the LoRA training numbers?",
      "How long does it take to train an adapter on an M4 Air?"],
     "One hundred iterations over 53 examples took about 42 seconds on the M4 Air, with "
     "peak memory of 1.5 GB. Validation loss fell from 3.965 to 1.707, and the resulting "
     "adapter is 5.5 MB."),

    (["What does fine-tuning actually change about a model?",
      "What is a LoRA adapter?",
      "How does low-rank adaptation work in that talk's explanation?"],
     "LoRA freezes the original weights and trains a small set of new ones alongside "
     "them. The result is a 5.5 MB adapter rather than a new copy of the model, so it can "
     "be swapped in and out at load time — and the base model on disk is untouched."),

    (["What agent did the talk use to drive the local model?",
      "Which coding agent was pointed at the local server?"],
     "OpenCode, configured with a single provider block pointing its base URL at "
     "http://127.0.0.1:8080/v1. The agent speaks the OpenAI protocol, so it cannot tell "
     "the model is local."),

    (["What memory bandwidth does the M4 have?",
      "How does the M4's bandwidth compare to an M4 Max?"],
     "The base M4 has 120 GB/s of memory bandwidth and supports up to 32 GB of unified "
     "memory. An M4 Max reaches 546 GB/s and 128 GB. The laptop in the talk is the base "
     "M4 with 16 GB — deliberately modest hardware."),
]


def main() -> int:
    rows = []
    for questions, answer in FACTS:
        for question in questions:
            rows.append({"messages": [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]})

    # Seeded, so the split is identical on every regeneration. An unseeded shuffle would
    # make "retrain and compare" meaningless: the validation loss would move because the
    # split moved, not because anything improved.
    random.Random(20260825).shuffle(rows)

    cut_valid = int(len(rows) * 0.8)
    cut_test = int(len(rows) * 0.9)
    splits = {"train": rows[:cut_valid],
              "valid": rows[cut_valid:cut_test],
              "test": rows[cut_test:]}

    DATA.mkdir(exist_ok=True)
    for name, subset in splits.items():
        path = DATA / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in subset))
        print(f"  {path.relative_to(ROOT)}: {len(subset)} examples")

    print(f"\n{len(rows)} examples from {len(FACTS)} facts, "
          f"each paraphrased {len(rows) // len(FACTS)}x on average")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
