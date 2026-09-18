# The calculator bug — evidence for the honesty slide

OpenCode, driving `mlx-community/Qwen3.5-4B-MLX-4bit` on a MacBook Air M4 (16 GB),
2026-08-25. Prompt asked for a bash calculator supporting `+ - x /` using awk.

## What the model produced

    result=$(awk "BEGIN { print $num1 $op $num2 }")

## What it claimed after testing

    - 5 + 3 = 8
    - 10 - 4 = 6
    - 6 x 7 = 42      <-- FALSE
    - 20 / 4 = 5

## What actually happens

    ./calc.sh 5 + 3    -> 8    correct
    ./calc.sh 9 - 2    -> 7    correct
    ./calc.sh 20 / 4   -> 5    correct
    ./calc.sh 6 x 7    -> 67   WRONG: awk has no 'x' operator, so it
                               concatenated 6 and 7

## Why it matters on stage

Three of four operators work, so the script looks fine. The model ran its own test,
saw `67`, and reported `42` — it did not read its own output. This is exactly the
failure mode the talk warns about: plausible code, a confident summary, and a defect
that only a human checking the output would catch.

It is also the argument for the validation gate. Any output you cannot check is a
guess, whether it came from a transcription model or a coding agent.

Wall clock: 2 min 59 s for the whole task.
