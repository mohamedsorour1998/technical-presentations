#!/usr/bin/env python3
"""The architecture slide's diagram: a draw.io file with the official AWS icons.

    .venv-deck/bin/python talks/devops-hackathon-final/architecture/make_architecture.py

Writes `architecture.drawio` (open it in draw.io to edit by hand) and renders
`architecture.png` with the draw.io desktop CLI, which the deck embeds.

WHY AN IMAGE, against deckkit's "draw charts as shapes" rule: the official AWS
icons exist only as draw.io stencils, and an AWS-style diagram without them reads
as a box chart. Rendered at 3x so a projector's rescale stays sharp.

EVERY BOX IS A CLAIM. Checked against TheAgentOrg's CLAUDE.md on 2026-09-24. In
particular the pipeline does NOT keep run state in `theagentorg-runs` --
`STATE_BACKEND` is `local` and the state travels job to job as an Actions
artifact -- so the only table drawn is `theagentorg-tenancy`, which every
credentialled job writes and the product reads.
"""

from __future__ import annotations

import base64
import pathlib
import subprocess
import sys
from xml.sax.saxutils import escape, quoteattr

HERE = pathlib.Path(__file__).resolve().parent
DRAWIO = pathlib.Path.home() / "Applications/draw.io.app/Contents/MacOS/draw.io"
GITHUB_MARK = HERE / "github-mark.svg"     # @primer/octicons 19.38.0, mark-github-24

# The deck's palette, which is the product's (web/app/globals.css).
BG, RAISED, BORDER, INK, DIM, CYAN = "#0B0F17", "#131A25", "#2C3A4F", "#E8ECF3", "#8B97AB", "#22D3EE"
FONT = "Helvetica Neue"

# AWS Architecture Icons category colours.
COMPUTE, INTEGRATION, DATABASE, SECURITY, AI, MANAGEMENT = (
    "#ED7100", "#E7157B", "#C925D1", "#DD344C", "#01A88D", "#E7157B")

W, H = 1560, 800
cells: list[str] = []


def _cell(id_, value, style, x, y, w, h):
    cells.append(f'<mxCell id="{id_}" value={quoteattr(value)} style={quoteattr(style)} '
                 f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" '
                 f'height="{h}" as="geometry"/></mxCell>')


def area(id_, x, y, w, h, label, *, stroke=BORDER, dashed=True, size=18, indent=12,
         colour=DIM, shape="rounded=1;arcSize=2;"):
    _cell(id_, f"<b>{escape(label)}</b>",
          f"{shape}html=1;whiteSpace=wrap;fillColor=none;strokeColor={stroke};"
          f"dashed={int(dashed)};verticalAlign=top;align=left;spacingLeft={indent};"
          f"spacingTop=4;fontColor={colour};fontSize={size};fontFamily={FONT};container=0;",
          x, y, w, h)


def icon(id_, res, x, y, title, detail, colour, size=60, *, label_above=False):
    """An AWS service icon. The label is NOT wrapped to the icon's width -- lines
    break only where `<br>` says -- and sits above the icon when an arrow must
    leave from its bottom."""
    label = f"<b>{escape(title)}</b><br>{escape(detail)}" if detail else f"<b>{escape(title)}</b>"
    where = ("verticalLabelPosition=top;verticalAlign=bottom;" if label_above
             else "verticalLabelPosition=bottom;verticalAlign=top;")
    _cell(id_, label,
          "sketch=0;outlineConnect=0;dashed=0;aspect=fixed;html=1;"
          f"fillColor={colour};strokeColor=#ffffff;{where}"
          f"align=center;fontColor={INK};fontSize=17;fontFamily={FONT};"
          f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{res};", x, y, size, size)


def person(id_, x, y, label, *, position="bottom"):
    where = {
        "bottom": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
        "left": "labelPosition=left;verticalLabelPosition=middle;align=right;"
                "verticalAlign=middle;spacingRight=8;",
        "right": "labelPosition=right;verticalLabelPosition=middle;align=left;"
                 "verticalAlign=middle;spacingLeft=8;",
    }[position]
    _cell(id_, f"<b>{escape(label)}</b>",
          f"sketch=0;outlineConnect=0;dashed=0;html=1;aspect=fixed;shape=mxgraph.aws4.user;"
          f"fillColor={INK};strokeColor=none;{where}fontColor={INK};fontSize=17;"
          f"fontFamily={FONT};", x, y, 46, 46)


def box(id_, x, y, w, h, label, *, stroke=BORDER, fill=RAISED, colour=INK, size=15,
        mono=False, shape="rounded=1;arcSize=12;"):
    font = "Menlo" if mono else FONT
    _cell(id_, label, f"{shape}html=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};"
          f"strokeWidth=1.5;fontColor={colour};fontSize={size};fontFamily={font};", x, y, w, h)


def edge(id_, src, tgt, label="", *, dashed=False, points=(), style="", at=0.0):
    """`at` slides the label along the edge, -1 (source end) to 1 (target end)."""
    pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points)
    inner = f'<Array as="points">{pts}</Array>' if pts else ""
    geo = f'<mxGeometry x="{at}" relative="1" as="geometry">{inner}</mxGeometry>'
    st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endSize=7;jumpStyle=arc;jumpSize=10;"
          f"strokeColor={DIM};strokeWidth=1.6;dashed={int(dashed)};fontColor={INK};"
          f"fontSize=15;fontFamily={FONT};labelBackgroundColor={BG};" + style)
    cells.append(f'<mxCell id="{id_}" value={quoteattr(label)} style={quoteattr(st)} '
                 f'edge="1" parent="1" source="{src}" target="{tgt}">{geo}</mxCell>')


def badge(n, x, y):
    """A numbered step, the way AWS reference architectures mark the flow."""
    _cell(f"step{n}", f"<b>{n}</b>",
          f"ellipse;html=1;fillColor={CYAN};strokeColor=none;fontColor=#07090C;"
          f"fontSize=16;fontFamily={FONT};", x, y, 28, 28)


def github_mark(x, y, size=30):
    svg = GITHUB_MARK.read_text().replace("<path ", f'<path fill="{INK}" ', 1)
    data = base64.b64encode(svg.encode()).decode()
    _cell("ghmark", "", f"shape=image;html=1;aspect=fixed;image=data:image/svg+xml,{data};",
          x, y, size, size)


# ── the diagram ───────────────────────────────────────────────────────────────

AWS_GROUP = ("points=[];outlineConnect=0;shape=mxgraph.aws4.group;"
             "grIcon=mxgraph.aws4.group_aws_cloud_alt;")
STAGES = ["plan", "gate1", "develop", "gate2", "sre", "gate3", "promote"]


def layout():
    # Groups first, so they sit behind everything drawn over them.
    area("gh", 10, 92, 440, 700, "GitHub", stroke=DIM, dashed=False, indent=44, colour=INK)
    area("aws", 470, 70, 1080, 722, "AWS Cloud · us-east-1", stroke=DIM, dashed=False,
         indent=34, colour=INK, shape=AWS_GROUP)
    area("product", 500, 112, 1020, 160, "The product")
    area("ingress", 500, 292, 1020, 150, "Ingress · state")
    area("agents", 500, 462, 1020, 320, "Agents")
    area("actions", 40, 212, 380, 490, "GitHub Actions · run-pipeline.yml", size=16)
    github_mark(20, 97)

    # ── GitHub: the issue, the seven jobs, the three gates, the pull request ──
    box("issue", 40, 140, 380, 52, "<b>auth-service</b> · an issue is opened")
    for i, name in enumerate(STAGES):
        gate = name.startswith("gate")
        box(f"job_{name}", 200, 250 + i * 56, 200, 42, name,
            stroke=CYAN if gate else BORDER, fill=BG if gate else RAISED,
            colour=CYAN if gate else INK, mono=True, size=16)
        if i:
            edge(f"seq{i}", f"job_{STAGES[i - 1]}", f"job_{name}")
    person("rev", 70, 416, "Reviewer")
    # Each approval gets its own lane; drawn straight they ran down the job chain.
    edge("approve_gate1", "rev", "job_gate1", dashed=True, points=[(150, 427.5), (150, 327)],
         style="exitX=1;exitY=0.25;entryX=0;entryY=0.5;endArrow=open;")
    edge("approve_gate2", "rev", "job_gate2", dashed=True,
         style="exitX=1;exitY=0.5;entryX=0;entryY=0.5;endArrow=open;")
    edge("approve_gate3", "rev", "job_gate3", dashed=True, points=[(150, 450.5), (150, 551)],
         style="exitX=1;exitY=0.75;entryX=0;entryY=0.5;endArrow=open;")
    box("pr", 40, 724, 380, 50, "<b>pull request</b> — opened by develop, merged by promote")
    edge("merge", "job_promote", "pr")

    # ── AWS. A row whose arrow must leave an icon's bottom puts that label above ──
    person("eng", 707, 8, "Engineer", position="right")
    icon("cognito", "cognito", 700, 160, "Amazon Cognito", "sign-in", SECURITY)
    icon("amplify", "amplify", 930, 160, "AWS Amplify",
         "Next.js · starts runs, approves gates", SECURITY, label_above=True)
    icon("role", "identity_and_access_management", 1160, 160, "IAM tenant role",
         "STS session tag", SECURITY)

    icon("lambda", "lambda", 600, 365, "AWS Lambda", "verifies HMAC-SHA256", COMPUTE,
         label_above=True)
    icon("eb", "eventbridge", 830, 365, "Amazon EventBridge", "rule: issues · opened",
         INTEGRATION, label_above=True)
    icon("sqs", "sqs", 1060, 365, "Amazon SQS", "dead-letter queue", INTEGRATION,
         label_above=True)
    icon("ddb", "dynamodb", 1340, 365, "Amazon DynamoDB",
         "run index · every stage writes it", DATABASE, label_above=True)

    icon("oidc", "identity_and_access_management", 560, 520, "IAM role via OIDC",
         "no static keys", SECURITY)
    icon("agentcore", "bedrock_agentcore", 800, 520, "Bedrock AgentCore",
         "5 runtimes · one per agent", AI, label_above=True)
    icon("nova", "nova2", 1040, 520, "Amazon Nova 2 Lite", "via Amazon Bedrock", AI)
    icon("secrets", "secrets_manager", 1340, 520, "Secrets Manager",
         "webhook secret · tokens", SECURITY)
    icon("ecr", "ecr", 560, 670, "Amazon ECR", "one arm64 image", COMPUTE)
    icon("cw", "cloudwatch_2", 1340, 670, "Amazon CloudWatch", "logs", MANAGEMENT)
    box("rule", 690, 660, 480, 92,
        "<b>security runtime</b><br>gitleaks · Trivy · Semgrep → fixed threshold"
        "<br>pass or block — <b>no model</b>",
        stroke=CYAN, fill=BG, size=17,
        shape="shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;size=26;")

    # ── the request's path, numbered the way AWS reference architectures do ──
    edge("e1", "eng", "issue", "open an issue", points=[(230, 31)],
         style="exitX=0;exitY=0.5;entryX=0.5;entryY=0;", at=-0.16)
    edge("e2", "issue", "lambda", "signed webhook", points=[(440, 166), (440, 395)],
         style="exitX=1;exitY=0.5;entryX=0;entryY=0.5;", at=0.61)
    edge("e2b", "lambda", "eb", "PutEvents")
    edge("dlq", "eb", "sqs", "on failure", dashed=True)
    edge("e3", "eb", "actions", "workflow_dispatch", points=[(860, 452)],
         style="exitX=0.5;exitY=1;entryX=1;entryY=0.49;", at=0.3)
    edge("e4", "actions", "oidc", "assume role", style="exitX=1;exitY=0.69;")
    edge("e4b", "oidc", "agentcore", "invoke")
    edge("e5", "agentcore", "nova", "prompt")
    edge("e6", "agentcore", "rule", "security stage",
         style="exitX=0.5;exitY=1;entryX=0.2917;entryY=0;")

    # ── the product ──
    edge("signin", "eng", "cognito", "sign in",
         style="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    edge("c2a", "cognito", "amplify")
    edge("a2r", "amplify", "role", "AssumeRole")
    edge("r2d", "role", "ddb", "own partition only", points=[(1510, 190), (1510, 395)],
         style="exitX=1;exitY=0.5;entryX=1;entryY=0.5;", at=-0.4)
    edge("app", "amplify", "actions", "start a run · approve a gate", points=[(960, 282)],
         style="exitX=0.5;exitY=1;entryX=1;entryY=0.1429;", at=0.2)

    for n, (x, y) in enumerate([(535, 17), (478, 404), (662, 438), (476, 512),
                                (985, 520), (738, 606), (40, 428), (1478, 150)], start=1):
        badge(n, x, y)


def main() -> int:
    layout()
    xml = ('<mxfile host="make_architecture.py"><diagram name="architecture" id="arch">'
           f'<mxGraphModel grid="0" page="0" pageWidth="{W}" pageHeight="{H}" '
           f'background="{BG}"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
           + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>")
    src = HERE / "architecture.drawio"
    src.write_text(xml, encoding="utf-8")
    out = HERE / "architecture.png"
    run = subprocess.run([str(DRAWIO), "--export", "--format", "png", "--scale", "3",
                          "--border", "12", "--output", str(out), str(src)],
                         capture_output=True, text=True, check=False)
    if run.returncode or not out.exists():
        print(run.stdout, run.stderr, file=sys.stderr)
        return 1
    print(f"{src.name}: {len(cells)} cells   {out.name}: {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
