#!/usr/bin/env python3
"""Record this talk's demonstrations. Content only — the engine is deckkit/record.py.

    .venv-deck/bin/python talks/bringing-the-model-home/record_demo.py transcribe
    .venv-deck/bin/python talks/bringing-the-model-home/record_demo.py agent --reuse
    .venv-deck/bin/python talks/bringing-the-model-home/record_demo.py --list

`--reuse` re-renders from the captured output in bench/recorded-output.json instead of
re-executing. Use it for any change to how a frame looks: rendering and running are
different problems, and one of these demos calls a model server that took 65 seconds on
a good day and thirteen minutes on the day it stopped responding mid-request.

To record a different talk's demos: copy this file, write new demo functions, and leave
the engine alone.
"""

from __future__ import annotations

import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from deckkit import record
from deckkit.record import Session, cli, run, _strip_ansi

ROOT = pathlib.Path(__file__).resolve().parent
record.OUT_DIR = ROOT / "pitch" / "video"

# ── the demos ─────────────────────────────────────────────────────────────────
# Each returns after running its real commands. The text that reaches the frames is the
# captured stdout of those runs, trimmed only to remove progress bars and the Hugging Face
# cache chatter, neither of which is part of the result.

MLX_GEN = "/opt/homebrew/bin/mlx_lm.generate"
MLX_LORA = "/opt/homebrew/bin/mlx_lm.lora"
WHISPER = str(pathlib.Path.home() / ".local/bin/mlx_whisper")
NO_THINK = '{"enable_thinking": false}'


def _answer(raw: str) -> str:
    """The model's reply, between mlx_lm.generate's two rules of '='."""
    parts = raw.split("==========")
    return parts[1].strip() if len(parts) > 1 else raw.strip()


def demo_transcribe(session: Session) -> None:
    """Demonstration 1 — transcription with the network off."""
    command = ("mlx_whisper clips/demo-60s.wav "
               "--model mlx-community/whisper-large-v3-mlx "
               "--language en --condition-on-previous-text False "
               "--output-dir bench --output-name recorded --output-format txt "
               "--verbose False")
    session.type_command("mlx_whisper clips/demo-60s.wav \\",
                         "--model mlx-community/whisper-large-v3-mlx \\",
                         "--language en --condition-on-previous-text False \\",
                         "--output-dir bench --output-format txt")
    _, elapsed = run(command.split())
    session.wait(elapsed, "transcribing")

    words = len((ROOT / "bench" / "recorded.txt").read_text().split())
    session.output(f"wrote bench/recorded.txt  ({words} words)", kind="ok")
    session.output("", kind="note")
    session.output("# 60 s of audio, no network, no credentials", kind="note")
    session.hold()


def demo_quantize(session: Session) -> None:
    """Quantization — the two sizes on disk, then the smaller model generating."""
    session.type_command("du -sh models--mlx-community--Qwen3-0.6B-bf16")
    out, _ = run(["zsh", "-c",
                  "du -sh ~/.cache/huggingface/hub/"
                  "models--mlx-community--Qwen3-0.6B-bf16 | cut -f1"])
    session.output(f"{out.strip()}     bfloat16")

    session.type_command("du -sh models/qwen3-0.6b-4bit")
    out, _ = run(["zsh", "-c", "du -sh models/qwen3-0.6b-4bit | cut -f1"])
    session.output(f"{out.strip()}    4-bit  —  3.4x smaller", kind="ok")

    command = [MLX_GEN, "--model", "models/qwen3-0.6b-4bit",
               "--prompt", "What is 2+2? Answer with just the number.",
               "--chat-template-config", NO_THINK, "--max-tokens", "20"]
    session.type_command("mlx_lm.generate --model models/qwen3-0.6b-4bit \\",
                         '--prompt "What is 2+2? Answer with just the number."')
    raw, elapsed = run(command)
    session.wait(elapsed, "generating")
    session.output(_answer(raw), kind="ok")
    for line in raw.split("\n"):
        if "tokens-per-sec" in line and "Generation" in line:
            session.output(line.strip())
        if "Peak memory" in line:
            session.output(line.strip())
    session.hold()


def demo_finetune(session: Session) -> None:
    """Fine-tuning — the base model's answer, the training run, then the adapter's."""
    question = "Who gave the talk Bringing the Model Home?"

    session.type_command("mlx_lm.generate --model models/qwen3-0.6b-4bit \\",
                         f'--prompt "{question}"')
    raw, elapsed = run([MLX_GEN, "--model", "models/qwen3-0.6b-4bit",
                        "--prompt", question, "--chat-template-config", NO_THINK,
                        "--max-tokens", "45"])
    session.wait(elapsed, "generating")
    session.output(_answer(raw)[:240], kind="bad")

    shutil.rmtree(ROOT / "adapters-0.6b", ignore_errors=True)
    session.type_command("mlx_lm.lora --model models/qwen3-0.6b-4bit --train \\",
                         "--data data --iters 100 --adapter-path adapters-0.6b")
    raw, elapsed = run([MLX_LORA, "--model", "models/qwen3-0.6b-4bit", "--train",
                        "--data", "data", "--iters", "100", "--batch-size", "4",
                        "--num-layers", "8", "--learning-rate", "2e-4",
                        "--mask-prompt", "--adapter-path", "adapters-0.6b",
                        "--steps-per-eval", "50"])
    for line in raw.replace("\r", "\n").split("\n"):
        if line.startswith("Iter ") and "Val loss" in line:
            session.output(line.strip())
    session.wait(elapsed, "training")
    session.output("saved adapters-0.6b/adapters.safetensors  (5.5 MB)", kind="ok")

    session.type_command("mlx_lm.generate --model models/qwen3-0.6b-4bit \\",
                         "--adapter-path adapters-0.6b \\",
                         f'--prompt "{question}"')
    raw, elapsed = run([MLX_GEN, "--model", "models/qwen3-0.6b-4bit",
                        "--adapter-path", "adapters-0.6b", "--prompt", question,
                        "--chat-template-config", NO_THINK, "--max-tokens", "45"])
    session.wait(elapsed, "generating")
    session.output(_answer(raw), kind="ok")
    session.hold()


def demo_agent(session: Session) -> None:
    """Demonstration 2 — an off-the-shelf agent driving the local model.

    One round trip is the whole demonstration: the agent receives a question it cannot
    answer from the prompt alone, chooses a tool, runs it, and answers from the result.
    Every turn of that happens against a model on this laptop.
    """
    session.output("# the model server is already running on 127.0.0.1:8080", kind="note")
    session.type_command('opencode run "How many words are in bench/full-6min.txt?"')
    out, elapsed = run(["opencode", "run",
                        "How many words are in bench/full-6min.txt?"],
                       env={"PATH": _NODE_PATH})
    session.wait(elapsed, "the agent working")

    # REASSEMBLED IN CAUSAL ORDER. OpenCode writes its final answer before the tool trace
    # when its output is piped rather than attached to a terminal; interactively the order
    # is command, result, answer. Replaying the piped order would show the agent answering
    # before it looked anything up, inverting the one thing this recording demonstrates.
    lines = [_strip_ansi(line).rstrip() for line in out.split("\n")]
    lines = [line for line in lines
             if line.strip() and not line.strip().startswith(">")]

    steps: list[tuple[str, str]] = []
    answer: list[str] = []
    index = 0
    while index < len(lines):
        text = lines[index].strip()
        if text.startswith("$ "):
            result = lines[index + 1].strip() if index + 1 < len(lines) else ""
            steps.append((text, result))
            index += 2
        else:
            answer.append(text)
            index += 1

    for command, result in steps:
        session.output(command, kind="out")
        if result:
            session.output(result, kind="out")
    for text in answer:
        session.output(text, kind="ok")

    session.output("", kind="note")
    session.output("# the agent chose the tool, ran it, then answered", kind="note")
    session.hold()


_NODE_PATH = ("/Users/sorour/.nvm/versions/node/v24.19.0/bin:"
              "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin")


DEMOS = {
    "quantize": demo_quantize,
    "finetune": demo_finetune,
    "transcribe": demo_transcribe,
    "agent": demo_agent,
}




if __name__ == "__main__":
    sys.exit(cli(DEMOS, out_dir=ROOT / "pitch" / "video"))
