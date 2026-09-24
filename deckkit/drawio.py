#!/usr/bin/env python3
"""deckkit.drawio — architecture diagrams as draw.io files, styled as AWS reference
architectures, rendered to PNG for a slide.

    from deckkit import drawio

    d = drawio.Diagram(1560, 800, theme=drawio.Theme.from_deck())
    d.aws_cloud("aws", 470, 70, 1080, 722, "AWS Cloud · us-east-1")
    d.icon("fn", "lambda", 560, 300, "AWS Lambda", "verifies HMAC", drawio.AWS["compute"])
    d.edge("e1", "src", "fn", "signed webhook")
    d.badge(1, 480, 290)
    drawio.build(d, HERE / "architecture")     # writes .drawio, checks icons, renders .png

WHY AN IMAGE AT ALL. deckkit draws charts as vector shapes, because a projector
softens a raster. An architecture diagram is the one exception. AWS does publish its
icons as SVG and PNG, but python-pptx cannot place an SVG, and placing icons and routing
arrows by hand in slide shapes is what produced an unreadable box chart. draw.io ships
the whole AWS library as named stencils, routes orthogonal connectors, and renders from a
CLI. Render at --scale 3 so the projector's rescale stays sharp.

WHY A SCRIPT, NOT A HAND-DRAWN FILE. Coordinates in code make a layout change a diff
somebody can review, and the diagram regenerates when the system changes. The written
`.drawio` still opens in draw.io for a hand edit; re-running the script overwrites it.

THE ICON NAME IS CHECKED, BECAUSE A WRONG ONE FAILS SILENTLY. An unknown `resIcon`
renders as a plain coloured square and draw.io raises nothing. `build()` reads the names
out of draw.io's own shape library and refuses a diagram that uses one it lacks.
"""

from __future__ import annotations

import base64
import functools
import mmap
import pathlib
import re
import shutil
import subprocess
from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr

# ── AWS Architecture Icons, Release 16 (2023-04-28) ─────────────────────────────
# Category -> colour, per AWS Labs' aws-icons-for-plantuml (AWSSymbols.md). Confirmed
# against the official icon deck before this table was written; re-check at
# https://aws.amazon.com/architecture/icons/ when a new release ships.
AWS = {
    "compute": "#ED7100", "containers": "#ED7100",                        # Smile
    "integration": "#E7157B", "management": "#E7157B",                   # Cosmos
    "database": "#C925D1", "devtools": "#C925D1",                        # Nebula
    "security": "#DD344C", "frontend": "#DD344C",                        # Mars
    "ai": "#01A88D", "migration": "#01A88D",                             # Orbit
    "storage": "#7AA116", "iot": "#7AA116",                              # Endor
    "networking": "#8C4FFF", "analytics": "#8C4FFF", "serverless": "#8C4FFF",  # Galaxy
}

# The AWS Cloud group: a solid border and the AWS logo in its corner. Sub-groups
# (a region, an area of the system) are dashed.
AWS_CLOUD_SHAPE = ("points=[];outlineConnect=0;shape=mxgraph.aws4.group;"
                   "grIcon=mxgraph.aws4.group_aws_cloud_alt;")


@dataclass(frozen=True)
class Theme:
    """The diagram's colours. Match the deck's, so the slide reads as one surface."""
    bg: str = "#14181F"
    raised: str = "#1C2230"
    border: str = "#2C3A4F"
    ink: str = "#E8EDF4"
    dim: str = "#8A94A6"
    accent: str = "#4FD1C5"
    on_accent: str = "#07090C"        # text drawn ON an accent fill: the step badges
    font: str = "Helvetica Neue"
    mono: str = "Menlo"

    @classmethod
    def from_deck(cls, **overrides) -> "Theme":
        """The deck's CURRENT palette, read at call time -- after a talk has called
        deck.palette() -- so the diagram and the slides cannot drift apart."""
        from deckkit import deck
        hexed = {"bg": deck.SLATE, "raised": deck.RAISED, "ink": deck.INK,
                 "dim": deck.DIM, "accent": deck.CYAN}
        return cls(**{k: f"#{v}" for k, v in hexed.items()}, **overrides)


# ── draw.io itself ─────────────────────────────────────────────────────────────

_SEARCHED = (pathlib.Path.home() / "Applications/draw.io.app/Contents/MacOS/draw.io",
             pathlib.Path("/Applications/draw.io.app/Contents/MacOS/draw.io"))


def find_drawio() -> pathlib.Path:
    """The draw.io desktop binary. Raises naming every place it looked, so "not found"
    is never read as "not installed" -- see CLAUDE.md, Part 3, for installing it."""
    for path in _SEARCHED:
        if path.exists():
            return path
    for name in ("drawio", "draw.io"):
        if found := shutil.which(name):
            return pathlib.Path(found)
    places = ", ".join(str(p) for p in _SEARCHED)
    raise FileNotFoundError(f"draw.io desktop not found in {places}, or on PATH as "
                            "`drawio`/`draw.io`. Install it: CLAUDE.md, Part 3.")


@functools.lru_cache(maxsize=1)
def available_icons() -> frozenset[str]:
    """Every AWS4 name draw.io's shape library offers. Read from the app itself,
    because that is what decides what renders -- not a web page.

    TWO PATTERNS, AND THE FIRST ALONE IS WRONG. Older names appear as literal
    `mxgraph.aws4.<name>`. Newer resource icons -- `bedrock_agentcore`, `nova2` -- are
    built at runtime in the minified sidebar as `resIcon="+d+".<name>` with
    `d="mxgraph.aws4"`, so the full name never appears as one string. Scanning only the
    literal pattern reported both as missing while both rendered correctly; `resIcon`
    is a style key only the AWS4 library uses, which is what scopes the second one."""
    binary = find_drawio()
    bundle = binary.parents[1] / "Resources" / "app.asar"
    if not bundle.exists():
        return frozenset()                      # unknown layout: the check is skipped
    with open(bundle, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        literal = re.findall(rb"mxgraph\.aws4\.([a-z0-9_]+)", m)
        built = re.findall(rb'resIcon="\+\w+\+"\.([a-z0-9_]+)', m)
    return frozenset(n.decode() for n in literal + built)


def label_points(px: float, *, canvas_width_px: float, slide_width_in: float) -> float:
    """A label's size on the SLIDE, in points, once the canvas is scaled to fit it.
    Measure this before presenting; the reference diagram's edge labels were 8.1pt."""
    return px / (canvas_width_px / slide_width_in) * 72


# ── the diagram ───────────────────────────────────────────────────────────────

class Diagram:
    """A draw.io page built in code. Draw GROUPS FIRST: cells are painted in the order
    they are added, so a group added last covers everything inside it."""

    def __init__(self, width: int, height: int, *, theme: Theme | None = None,
                 name: str = "architecture", host: str = "deckkit.drawio"):
        self.width, self.height = width, height
        self.theme = theme or Theme()
        self.name, self.host = name, host
        self.cells: list[str] = []
        self.icons: set[str] = set()

    def _cell(self, id_, value, style, x, y, w, h):
        self.cells.append(
            f'<mxCell id="{id_}" value={quoteattr(value)} style={quoteattr(style)} '
            f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" '
            f'height="{h}" as="geometry"/></mxCell>')

    # ── containers ──
    def area(self, id_, x, y, w, h, label, *, stroke=None, dashed=True, size=18, indent=12,
             colour=None, shape="rounded=1;arcSize=2;"):
        """A labelled group: an area of the system, drawn dashed. Label top-left."""
        t = self.theme
        self._cell(id_, f"<b>{escape(label)}</b>",
                   f"{shape}html=1;whiteSpace=wrap;fillColor=none;"
                   f"strokeColor={stroke or t.border};dashed={int(dashed)};verticalAlign=top;"
                   f"align=left;spacingLeft={indent};spacingTop=4;fontColor={colour or t.dim};"
                   f"fontSize={size};fontFamily={t.font};container=0;", x, y, w, h)

    def aws_cloud(self, id_, x, y, w, h, label="AWS Cloud", *, indent=34):
        """The outermost AWS group: solid border, the AWS logo in the corner."""
        self.icons.add("group_aws_cloud_alt")
        self.area(id_, x, y, w, h, label, stroke=self.theme.dim, dashed=False,
                  indent=indent, colour=self.theme.ink, shape=AWS_CLOUD_SHAPE)

    # ── nodes ──
    def icon(self, id_, res, x, y, title, detail, colour, size=60, *, label_above=False):
        """An AWS service icon: `res` is the draw.io name after `mxgraph.aws4.`, and
        `colour` its category's, from AWS. The label is NOT wrapped to the icon's
        width -- lines break only at `<br>` -- and goes ABOVE the icon when an arrow
        must leave from its bottom, or the arrow runs through the text."""
        self.icons.add(res)
        t = self.theme
        label = (f"<b>{escape(title)}</b><br>{escape(detail)}" if detail
                 else f"<b>{escape(title)}</b>")
        where = ("verticalLabelPosition=top;verticalAlign=bottom;" if label_above
                 else "verticalLabelPosition=bottom;verticalAlign=top;")
        self._cell(id_, label,
                   "sketch=0;outlineConnect=0;dashed=0;aspect=fixed;html=1;"
                   f"fillColor={colour};strokeColor=#ffffff;{where}"
                   f"align=center;fontColor={t.ink};fontSize=17;fontFamily={t.font};"
                   f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{res};",
                   x, y, size, size)

    def person(self, id_, x, y, label, *, position="bottom"):
        """A human actor. `position` puts the label below, left or right of the figure;
        pick the side no arrow leaves from."""
        self.icons.add("user")
        t = self.theme
        where = {
            "bottom": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
            "left": "labelPosition=left;verticalLabelPosition=middle;align=right;"
                    "verticalAlign=middle;spacingRight=8;",
            "right": "labelPosition=right;verticalLabelPosition=middle;align=left;"
                     "verticalAlign=middle;spacingLeft=8;",
        }[position]
        self._cell(id_, f"<b>{escape(label)}</b>",
                   f"sketch=0;outlineConnect=0;dashed=0;html=1;aspect=fixed;"
                   f"shape=mxgraph.aws4.user;fillColor={t.ink};strokeColor=none;{where}"
                   f"fontColor={t.ink};fontSize=17;fontFamily={t.font};", x, y, 46, 46)

    def box(self, id_, x, y, w, h, label, *, stroke=None, fill=None, colour=None, size=15,
            mono=False, shape="rounded=1;arcSize=12;"):
        """A plain node: a step, a file, a job. `label` is HTML, so bold with <b>."""
        t = self.theme
        self._cell(id_, label,
                   f"{shape}html=1;whiteSpace=wrap;fillColor={fill or t.raised};"
                   f"strokeColor={stroke or t.border};strokeWidth=1.5;"
                   f"fontColor={colour or t.ink};fontSize={size};"
                   f"fontFamily={t.mono if mono else t.font};", x, y, w, h)

    def hexagon(self, id_, x, y, w, h, label, *, size=17):
        """YOUR OWN code, where no AWS icon applies -- a rule, a gate, a pure function.
        Borrowing an AWS icon for it would claim a managed service that is not there."""
        self.box(id_, x, y, w, h, label, stroke=self.theme.accent, fill=self.theme.bg,
                 size=size, shape="shape=hexagon;perimeter=hexagonPerimeter2;"
                                  "fixedSize=1;size=26;")

    def image(self, id_, svg: pathlib.Path, x, y, size=30, *, fill=None):
        """A vendor mark that is not an AWS icon (GitHub, a SaaS). Take the SVG from
        the vendor's own icon package, never retyped; `fill` recolours it for a dark
        page, since most marks ship black."""
        text = svg.read_text()
        if fill:
            text = text.replace("<path ", f'<path fill="{fill}" ', 1)
        data = base64.b64encode(text.encode()).decode()
        self._cell(id_, "", f"shape=image;html=1;aspect=fixed;image=data:image/svg+xml,"
                   f"{data};", x, y, size, size)

    # ── flow ──
    def edge(self, id_, src, tgt, label="", *, dashed=False, points=(), style="", at=0.0):
        """An orthogonal arrow. `points` are waypoints -- give each cross-group arrow a
        lane of its own. `style` pins exit/entry, e.g. "exitX=1;exitY=0.5;entryX=0;
        entryY=0.5;". `at` slides the label along the path, -1 (source) to 1 (target).
        Crossings draw as arcs, so two lines that must cross read as crossing."""
        t = self.theme
        pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points)
        inner = f'<Array as="points">{pts}</Array>' if pts else ""
        geo = f'<mxGeometry x="{at}" relative="1" as="geometry">{inner}</mxGeometry>'
        st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endSize=7;"
              "jumpStyle=arc;jumpSize=10;"
              f"strokeColor={t.dim};strokeWidth=1.6;dashed={int(dashed)};fontColor={t.ink};"
              f"fontSize=15;fontFamily={t.font};labelBackgroundColor={t.bg};" + style)
        self.cells.append(f'<mxCell id="{id_}" value={quoteattr(label)} '
                          f'style={quoteattr(st)} edge="1" parent="1" source="{src}" '
                          f'target="{tgt}">{geo}</mxCell>')

    def badge(self, n, x, y):
        """A numbered step, the way AWS reference architectures mark the request's
        path. Place it BESIDE its arrow's label, never on it."""
        t = self.theme
        self._cell(f"step{n}", f"<b>{n}</b>",
                   f"ellipse;html=1;fillColor={t.accent};strokeColor=none;"
                   f"fontColor={t.on_accent};fontSize=16;fontFamily={t.font};", x, y, 28, 28)

    # ── output ──
    def xml(self) -> str:
        return (f'<mxfile host="{self.host}"><diagram name="{self.name}" id="arch">'
                f'<mxGraphModel grid="0" page="0" pageWidth="{self.width}" '
                f'pageHeight="{self.height}" background="{self.theme.bg}"><root>'
                '<mxCell id="0"/><mxCell id="1" parent="0"/>'
                + "".join(self.cells) + "</root></mxGraphModel></diagram></mxfile>")

    def unknown_icons(self) -> list[str]:
        """Icon names draw.io does not have. Empty when the library cannot be read."""
        known = available_icons()
        return sorted(self.icons - known) if known else []


def render(src: pathlib.Path, png: pathlib.Path, *, scale: int = 3, border: int = 12) -> None:
    """Render a .drawio file to PNG with the draw.io desktop CLI. Headless; exits
    non-zero and leaves no PNG on failure, which is checked rather than assumed."""
    run = subprocess.run([str(find_drawio()), "--export", "--format", "png",
                          "--scale", str(scale), "--border", str(border),
                          "--output", str(png), str(src)],
                         capture_output=True, text=True, check=False)
    if run.returncode or not png.exists():
        raise RuntimeError(f"draw.io export failed ({run.returncode}):\n"
                           f"{run.stdout}\n{run.stderr}")


def build(diagram: Diagram, stem: pathlib.Path, *, scale: int = 3) -> tuple[pathlib.Path, pathlib.Path]:
    """Write <stem>.drawio, REFUSE unknown icon names, render <stem>.png. Then open the
    PNG and look at it: no check here can see an arrow through a label."""
    unknown = diagram.unknown_icons()
    if unknown:
        raise ValueError(f"draw.io has no icon named {unknown}; it would render as a blank "
                         "square. Look the name up: CLAUDE.md, Part 3.")
    src, png = stem.with_suffix(".drawio"), stem.with_suffix(".png")
    src.write_text(diagram.xml(), encoding="utf-8")
    render(src, png, scale=scale)
    print(f"{src.name}: {len(diagram.cells)} cells, {len(diagram.icons)} icon names checked"
          f"   {png.name}: {png.stat().st_size // 1024} KB")
    return src, png
