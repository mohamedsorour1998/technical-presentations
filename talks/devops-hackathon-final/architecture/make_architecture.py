#!/usr/bin/env python3
"""The architecture slide's diagram, styled as an AWS reference architecture.

    .venv-deck/bin/python talks/devops-hackathon-final/architecture/make_architecture.py

Layout only -- the primitives, the icon check and the render are deckkit/drawio.py.
Writes `architecture.drawio` (opens in draw.io for a hand edit) and renders
`architecture.png`, which slide_architecture embeds.

EVERY BOX IS A CLAIM. Checked against TheAgentOrg's CLAUDE.md on 2026-09-24. In
particular the pipeline does NOT keep run state in `theagentorg-runs` --
`STATE_BACKEND` is `local` and the state travels job to job as an Actions artifact --
so the only table drawn is `theagentorg-tenancy`, which every credentialled job writes
and the product reads.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from deckkit import drawio          # noqa: E402 -- the path insert must come first
from deckkit.drawio import AWS      # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
GITHUB_MARK = HERE / "github-mark.svg"     # @primer/octicons 19.38.0, mark-github-24

# The deck's palette, which is the product's own (TheAgentOrg web/app/globals.css).
# Explicit rather than Theme.from_deck(): this script runs without build_deck.py, so
# the talk's deck.palette() call has not happened when it does.
THEME = drawio.Theme(bg="#0B0F17", raised="#131A25", border="#2C3A4F", ink="#E8ECF3",
                     dim="#8B97AB", accent="#22D3EE")
STAGES = ["plan", "gate1", "develop", "gate2", "sre", "gate3", "promote"]


def diagram() -> drawio.Diagram:
    d, t = drawio.Diagram(1560, 800, theme=THEME, host="make_architecture.py"), THEME

    # Groups first, so they sit behind everything drawn over them.
    d.area("gh", 10, 92, 440, 700, "GitHub", stroke=t.dim, dashed=False, indent=44,
           colour=t.ink)
    d.aws_cloud("aws", 470, 70, 1080, 722, "AWS Cloud · us-east-1")
    d.area("product", 500, 112, 1020, 160, "The product")
    d.area("ingress", 500, 292, 1020, 150, "Ingress · state")
    d.area("agents", 500, 462, 1020, 320, "Agents")
    d.area("actions", 40, 212, 380, 490, "GitHub Actions · run-pipeline.yml", size=16)
    d.image("ghmark", GITHUB_MARK, 20, 97, fill=t.ink)

    # ── GitHub: the issue, the seven jobs, the three gates, the pull request ──
    d.box("issue", 40, 140, 380, 52, "<b>auth-service</b> · an issue is opened")
    for i, name in enumerate(STAGES):
        gate = name.startswith("gate")
        d.box(f"job_{name}", 200, 250 + i * 56, 200, 42, name,
              stroke=t.accent if gate else t.border, fill=t.bg if gate else t.raised,
              colour=t.accent if gate else t.ink, mono=True, size=16)
        if i:
            d.edge(f"seq{i}", f"job_{STAGES[i - 1]}", f"job_{name}")
    d.person("rev", 70, 416, "Reviewer")
    # Each approval gets its own lane; drawn straight they ran down the job chain.
    d.edge("approve_gate1", "rev", "job_gate1", dashed=True, points=[(150, 427.5), (150, 327)],
           style="exitX=1;exitY=0.25;entryX=0;entryY=0.5;endArrow=open;")
    d.edge("approve_gate2", "rev", "job_gate2", dashed=True,
           style="exitX=1;exitY=0.5;entryX=0;entryY=0.5;endArrow=open;")
    d.edge("approve_gate3", "rev", "job_gate3", dashed=True, points=[(150, 450.5), (150, 551)],
           style="exitX=1;exitY=0.75;entryX=0;entryY=0.5;endArrow=open;")
    d.box("pr", 40, 724, 380, 50, "<b>pull request</b> — opened by develop, merged by promote")
    d.edge("merge", "job_promote", "pr")

    # ── AWS. A row whose arrow must leave an icon's bottom puts that label above ──
    d.person("eng", 707, 8, "Engineer", position="right")
    d.icon("cognito", "cognito", 700, 160, "Amazon Cognito", "sign-in", AWS["security"])
    d.icon("amplify", "amplify", 930, 160, "AWS Amplify",
           "Next.js · starts runs, approves gates", AWS["frontend"], label_above=True)
    d.icon("role", "identity_and_access_management", 1160, 160, "IAM tenant role",
           "STS session tag", AWS["security"])

    d.icon("lambda", "lambda", 600, 365, "AWS Lambda", "verifies HMAC-SHA256",
           AWS["compute"], label_above=True)
    d.icon("eb", "eventbridge", 830, 365, "Amazon EventBridge", "rule: issues · opened",
           AWS["integration"], label_above=True)
    d.icon("sqs", "sqs", 1060, 365, "Amazon SQS", "dead-letter queue",
           AWS["integration"], label_above=True)
    d.icon("ddb", "dynamodb", 1340, 365, "Amazon DynamoDB",
           "run index · the pipeline writes it", AWS["database"], label_above=True)

    d.icon("oidc", "identity_and_access_management", 560, 520, "IAM role via OIDC",
           "no static keys", AWS["security"])
    d.icon("agentcore", "bedrock_agentcore", 800, 520, "Bedrock AgentCore",
           "planner · developer · reviewer · security · sre", AWS["ai"], label_above=True)
    d.icon("nova", "nova2", 1040, 520, "Amazon Nova 2 Lite", "Bedrock · US cross-region", AWS["ai"])
    d.icon("secrets", "secrets_manager", 1340, 520, "Secrets Manager",
           "webhook secret · tokens", AWS["security"])
    d.icon("ecr", "ecr", 560, 670, "Amazon ECR", "one arm64 image", AWS["containers"])
    d.icon("cw", "cloudwatch_2", 1340, 670, "Amazon CloudWatch", "logs", AWS["management"])
    # THE MODEL IS IN THE SECURITY RUNTIME, AND THE HEXAGON SAYS WHAT FOR. Asked of
    # the first version, which read "pass or block — no model" beside an arrow into
    # Nova: "I see an AI model, yet you say the security gate uses none?" Both were
    # true -- `security.run` decides with `compute_security_verdict`, THEN asks the
    # model for the explanation -- and the picture showed only the first half.
    d.hexagon("rule", 670, 660, 600, 92,
              "<b>security runtime</b>: gitleaks · Trivy · Semgrep → fixed threshold"
              "<br>pass or block is decided with <b>no model</b>"
              "<br>the model only writes the explanation, afterwards")

    # ── the request's path, numbered the way AWS reference architectures do ──
    d.edge("e1", "eng", "issue", "open an issue", points=[(230, 31)],
           style="exitX=0;exitY=0.5;entryX=0.5;entryY=0;", at=-0.16)
    d.edge("e2", "issue", "lambda", "signed webhook", points=[(440, 166), (440, 395)],
           style="exitX=1;exitY=0.5;entryX=0;entryY=0.5;", at=0.61)
    d.edge("e2b", "lambda", "eb", "PutEvents")
    d.edge("dlq", "eb", "sqs", "on failure", dashed=True)
    d.edge("e3", "eb", "actions", "workflow_dispatch", points=[(860, 452)],
           style="exitX=0.5;exitY=1;entryX=1;entryY=0.49;", at=0.3)
    d.edge("e4", "actions", "oidc", "assume role", style="exitX=1;exitY=0.69;")
    d.edge("e4b", "oidc", "agentcore", "invoke")
    d.edge("e5", "agentcore", "nova", "prompt")
    d.edge("e6", "agentcore", "rule", "security stage",
           style="exitX=0.5;exitY=1;entryX=0.2667;entryY=0;")

    # ── the product ──
    d.edge("signin", "eng", "cognito", "sign in",
           style="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    d.edge("c2a", "cognito", "amplify")
    d.edge("a2r", "amplify", "role", "AssumeRole")
    d.edge("r2d", "role", "ddb", "own partition only", points=[(1510, 190), (1510, 395)],
           style="exitX=1;exitY=0.5;entryX=1;entryY=0.5;", at=-0.4)
    d.edge("app", "amplify", "actions", "start a run · approve a gate", points=[(960, 282)],
           style="exitX=0.5;exitY=1;entryX=1;entryY=0.1429;", at=0.2)

    for n, (x, y) in enumerate([(535, 17), (478, 404), (662, 438), (476, 512),
                                (985, 520), (738, 606), (40, 428), (1478, 150)], start=1):
        d.badge(n, x, y)
    return d


if __name__ == "__main__":
    drawio.build(diagram(), HERE / "architecture")
