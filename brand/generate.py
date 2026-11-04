#!/usr/bin/env python3
"""Generate every Buildruntime brand asset from a single source of truth.

All text is converted to vector outlines, so the SVGs render identically on
GitHub, in browsers and in image viewers without needing any font installed.

Requirements (build machine only, not needed to view the assets):
    pip install fonttools uharfbuzz
    Inter (OFL-1.1)          https://rsms.me/inter/
    JetBrains Mono (OFL-1.1) https://www.jetbrains.com/lp/mono/
    Optional for PNG export: Node + Playwright with Chromium.

Usage:
    python3 brand/generate.py            # writes SVGs into assets/brand/
    node brand/export-png.js             # rasterises the PNG exports
"""

from __future__ import annotations

import os
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "brand"

FONT_DIRS = [
    Path(os.environ.get("BR_FONT_DIR", "")),
    Path("/usr/share/fonts/opentype/inter"),
    Path("/usr/share/fonts/truetype/jetbrains-mono"),
    Path.home() / ".fonts",
    Path("/Library/Fonts"),
]

# --------------------------------------------------------------------------
# Brand tokens. Keep in sync with brand/BRAND.md.
# --------------------------------------------------------------------------
INK_950 = "#0B0F17"   # primary dark / tile
INK_900 = "#121826"
INK_800 = "#1B2232"
INK_700 = "#283043"
SLATE_500 = "#5B6474"
SLATE_400 = "#8A94A6"
LINE = "#DCE1E8"
PAPER = "#F7F8FA"
WHITE = "#FFFFFF"
SIGNAL = "#FF5B2E"    # primary accent: "build"
SIGNAL_SOFT = "#FF8A5C"
RUN = "#2BD99F"       # secondary accent: "running"

THEMES = {
    "dark": dict(bg=INK_950, dots=INK_800, fg=PAPER, muted=SLATE_400,
                 rail=INK_700, node_fill=INK_900, watermark=WHITE, wm_op=0.035),
    "light": dict(bg=PAPER, dots=LINE, fg=INK_950, muted=SLATE_500,
                  rail=LINE, node_fill=WHITE, watermark=INK_950, wm_op=0.04),
}

# --------------------------------------------------------------------------
# Text -> outlines
# --------------------------------------------------------------------------
_font_cache: dict[str, tuple] = {}


def _find_font(filename: str) -> Path:
    for d in FONT_DIRS:
        p = d / filename
        if str(d) and p.exists():
            return p
    raise FileNotFoundError(f"Font {filename} not found; set BR_FONT_DIR")


def _load(filename: str):
    if filename not in _font_cache:
        path = _find_font(filename)
        blob = hb.Blob.from_file_path(str(path))
        face = hb.Face(blob)
        font = hb.Font(face)
        tt = TTFont(str(path))
        _font_cache[filename] = (font, tt, tt.getGlyphSet(), face.upem)
    return _font_cache[filename]


def text_outline(text: str, font_file: str, size: float, x: float, y: float,
                 tracking: float = 0.0, anchor: str = "start") -> tuple[str, float]:
    """Return (svg path data, advance width) for `text` set at baseline y.

    tracking is in em units (e.g. -0.02 for -2%).
    """
    font, tt, glyphset, upem = _load(font_file)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    scale = size / upem
    track = tracking * upem
    order = tt.getGlyphOrder()

    total = sum(p.x_advance + track for p in buf.glyph_positions) - track
    width = total * scale
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width

    parts = []
    pen_x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        svg_pen = SVGPathPen(glyphset, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        gx = x + (pen_x + pos.x_offset) * scale
        gy = y - pos.y_offset * scale
        glyphset[name].draw(TransformPen(svg_pen, (scale, 0, 0, -scale, gx, gy)))
        d = svg_pen.getCommands()
        if d:
            parts.append(d)
        pen_x += pos.x_advance + track
    return " ".join(parts), width


def text_el(text, font_file, size, x, y, fill, tracking=0.0, anchor="start",
            opacity=None) -> tuple[str, float]:
    d, w = text_outline(text, font_file, size, x, y, tracking, anchor)
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return f'<path fill="{fill}"{op} d="{d}"/>', w


DISPLAY = "InterDisplay-Bold.otf"
SANS_MED = "Inter-Medium.otf"
MONO = "JetBrainsMono-Medium.ttf"
MONO_BOLD = "JetBrainsMono-Bold.ttf"

WORDMARK_TRACKING = -0.035

# --------------------------------------------------------------------------
# The mark: a stepped chevron built from three blocks.
# Blocks = build stages; their forward offset = execution / runtime.
# Defined on a 64 x 64 grid.
# --------------------------------------------------------------------------
BARS = [  # x, y, w, h  (role)
    (13, 14.5, 24, 9, "outer"),
    (25, 27.5, 26, 9, "core"),
    (13, 40.5, 24, 9, "outer"),
]
BAR_RX = 2
TILE_RX = 14


def mark(x: float, y: float, size: float, outer: str, core: str,
         tile: str | None = None, tile_rx: float | None = TILE_RX,
         opacity: float | None = None) -> str:
    s = size / 64
    op = f' opacity="{opacity}"' if opacity is not None else ""
    out = [f'<g transform="translate({x:g} {y:g}) scale({s:g})"{op}>']
    if tile:
        rx = f' rx="{tile_rx}"' if tile_rx else ""
        out.append(f'<rect width="64" height="64"{rx} fill="{tile}"/>')
    for bx, by, bw, bh, role in BARS:
        fill = core if role == "core" else outer
        out.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="{BAR_RX}" fill="{fill}"/>')
    out.append("</g>")
    return "".join(out)


def svg(w, h, body, title, desc="") -> str:
    if not title:  # purely decorative
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                f'viewBox="0 0 {w} {h}" aria-hidden="true">{body}</svg>\n')
    d = f"<desc>{desc}</desc>" if desc else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">'
            f'<title id="t">{title}</title>{d}{body}</svg>\n')


def dot_grid(t, w, h, step=24, r=1.2, pid="dots") -> str:
    return (f'<defs><pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{step/2}" cy="{step/2}" r="{r}" fill="{t["dots"]}"/></pattern>'
            f'<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="1"/>'
            f'<stop offset="0.55" stop-color="#fff" stop-opacity="0.35"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
            f'<mask id="m"><rect width="{w}" height="{h}" fill="url(#fade)"/></mask></defs>'
            f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#{pid})" mask="url(#m)"/>')


STAGES = ["build", "test", "package", "deploy", "run"]


def pipeline(t, x0, x1, y, label_size=15) -> str:
    """The build -> run rail used across banners."""
    n = len(STAGES)
    step = (x1 - x0) / (n - 1)
    out = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{t["rail"]}" stroke-width="2"/>']
    # progress segment up to the last stage
    out.append(f'<line x1="{x0}" y1="{y}" x2="{x1 - step}" y2="{y}" stroke="{SIGNAL}" '
               f'stroke-width="2" stroke-opacity="0.55"/>')
    for i, name in enumerate(STAGES):
        cx = x0 + i * step
        last = i == n - 1
        if last:
            out.append(f'<circle cx="{cx}" cy="{y}" r="13" fill="{RUN}" fill-opacity="0.16"/>')
            out.append(f'<circle cx="{cx}" cy="{y}" r="6.5" fill="{RUN}"/>')
            color = RUN
        else:
            out.append(f'<rect x="{cx-7}" y="{y-7}" width="14" height="14" rx="2.5" '
                       f'fill="{t["node_fill"]}" stroke="{SIGNAL}" stroke-width="2"/>')
            out.append(f'<rect x="{cx-2.5}" y="{y-2.5}" width="5" height="5" rx="1" fill="{SIGNAL}"/>')
            color = t["muted"]
        el, _ = text_el(name, MONO, label_size, cx, y + 34, color, anchor="middle")
        out.append(el)
    return "".join(out)


# --------------------------------------------------------------------------
# Asset builders
# --------------------------------------------------------------------------
def build_marks():
    files = {
        "logo-mark.svg": mark(0, 0, 64, PAPER, SIGNAL, tile=INK_950),
        "logo-mark-on-light.svg": mark(0, 0, 64, INK_950, SIGNAL),
        "logo-mark-on-dark.svg": mark(0, 0, 64, PAPER, SIGNAL),
        "logo-mark-mono-black.svg": mark(0, 0, 64, INK_950, INK_950),
        "logo-mark-mono-white.svg": mark(0, 0, 64, WHITE, WHITE),
    }
    for name, body in files.items():
        (OUT / name).write_text(svg(64, 64, body, "Buildruntime"))


def build_wordmarks():
    size = 56
    for theme, fg in (("light", INK_950), ("dark", PAPER)):
        # horizontal lockup: tile + wordmark
        tile = 64
        gap = 18
        wm, w = text_el("buildruntime", DISPLAY, size, tile + gap, 52, fg,
                        tracking=WORDMARK_TRACKING)
        width = round(tile + gap + w + 2)
        body = mark(0, 0, tile, PAPER, SIGNAL, tile=INK_950) + wm
        (OUT / f"logo-horizontal-{theme}.svg").write_text(
            svg(width, 64, body, "Buildruntime"))
        # wordmark only
        wm, w = text_el("buildruntime", DISPLAY, size, 0, 52, fg, tracking=WORDMARK_TRACKING)
        (OUT / f"wordmark-{theme}.svg").write_text(
            svg(round(w + 2), 64, wm, "Buildruntime"))


def build_banner(theme: str):
    t = THEMES[theme]
    W, H = 1280, 400
    b = [dot_grid(t, W, H)]
    # watermark mark on the right
    b.append(mark(900, -20, 360, t["watermark"], t["watermark"], opacity=t["wm_op"]))
    # lockup
    b.append(mark(96, 92, 104, PAPER, SIGNAL, tile=INK_950, tile_rx=14))
    if theme == "dark":  # keep the tile edge visible on the dark canvas
        b.append(f'<rect x="97" y="93" width="102" height="102" rx="22.4" fill="none" '
                 f'stroke="{INK_700}" stroke-width="2"/>')
    wm, _ = text_el("buildruntime", DISPLAY, 88, 228, 172, t["fg"], tracking=WORDMARK_TRACKING)
    b.append(wm)
    tag, tw = text_el("from build to runtime", MONO, 24, 232, 214, t["muted"])
    b.append(tag)
    # blinking-cursor style block after the tagline
    b.append(f'<rect x="{232 + tw + 8}" y="194" width="12" height="24" rx="1.5" fill="{SIGNAL}"/>')
    b.append(pipeline(t, 112, 1168, 300))
    (OUT / f"banner-{theme}.svg").write_text(
        svg(W, H, "".join(b), "Buildruntime — from build to runtime",
            "Buildruntime logo with the tagline 'from build to runtime' and a pipeline: build, test, package, deploy, run."))


def build_social():
    t = THEMES["dark"]
    W, H = 1280, 640
    b = [dot_grid(t, W, H, pid="dots2")]
    b.append(mark(W / 2 - 64, 112, 128, PAPER, SIGNAL, tile=INK_950))
    b.append(f'<rect x="{W/2-64}" y="112" width="128" height="128" rx="28" fill="none" '
             f'stroke="{INK_700}" stroke-width="2"/>')
    wm, _ = text_el("buildruntime", DISPLAY, 104, W / 2, 352, t["fg"],
                    tracking=WORDMARK_TRACKING, anchor="middle")
    b.append(wm)
    tag, _ = text_el("from build to runtime", MONO, 28, W / 2, 404, t["muted"], anchor="middle")
    b.append(tag)
    b.append(pipeline(t, 240, 1040, 508, label_size=16))
    (OUT / "social-preview.svg").write_text(
        svg(W, H, "".join(b), "Buildruntime — from build to runtime"))


def build_avatar():
    S = 512
    body = (f'<rect width="{S}" height="{S}" fill="{INK_950}"/>'
            + mark(0, 0, S, PAPER, SIGNAL))
    (OUT / "avatar.svg").write_text(svg(S, S, body, "Buildruntime"))


def build_divider():
    """A thin rail used between README sections, in both themes."""
    for theme in ("light", "dark"):
        t = THEMES[theme]
        W, H = 1280, 24
        b = [f'<line x1="0" y1="12" x2="{W}" y2="12" stroke="{t["rail"]}" stroke-width="2"/>',
             f'<line x1="0" y1="12" x2="160" y2="12" stroke="{SIGNAL}" stroke-width="2"/>',
             f'<rect x="160" y="6" width="12" height="12" rx="2" fill="{SIGNAL}"/>']
        (OUT / f"divider-{theme}.svg").write_text(svg(W, H, "".join(b), "", ""))


PALETTE = [
    ("Ink 950", INK_950, PAPER), ("Ink 700", INK_700, PAPER),
    ("Slate 400", SLATE_400, INK_950), ("Paper", PAPER, INK_950),
    ("Signal", SIGNAL, INK_950), ("Run", RUN, INK_950),
]


def build_palette():
    W, sw, gap, H = 1280, 200, 16, 168
    x0 = (W - (len(PALETTE) * sw + (len(PALETTE) - 1) * gap)) / 2
    b = []
    for i, (name, hexv, ink) in enumerate(PALETTE):
        x = x0 + i * (sw + gap)
        b.append(f'<rect x="{x}" y="0.5" width="{sw}" height="{H-1}" rx="14" fill="{hexv}" '
                 f'stroke="{LINE}" stroke-opacity="0.6"/>')
        el, _ = text_el(name, SANS_MED, 20, x + 18, H - 52, ink)
        b.append(el)
        el, _ = text_el(hexv, MONO, 16, x + 18, H - 24, ink, opacity=0.75)
        b.append(el)
    (OUT / "palette.svg").write_text(svg(W, H, "".join(b), "Buildruntime colour palette"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_palette()
    build_marks()
    build_wordmarks()
    build_banner("dark")
    build_banner("light")
    build_social()
    build_avatar()
    build_divider()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    main()
