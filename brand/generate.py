#!/usr/bin/env python3
"""Generate the Buildruntime brand assets from one set of tokens.

Every piece of text is converted to vector outlines, so the SVGs look the same
on GitHub, in browsers and in image viewers, with no fonts installed.

Setup (build machine only; viewers need nothing):
    pip install fonttools uharfbuzz brotli
    npm i --prefix brand/.cache @fontsource/schibsted-grotesk @fontsource/ibm-plex-mono

Usage:
    python3 brand/generate.py     # SVGs -> assets/brand/
    node brand/export-png.js      # PNG exports (needs Playwright + Chromium)
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
CACHE = ROOT / "brand" / ".cache"
FONTSOURCE = CACHE / "node_modules" / "@fontsource"

# ---------------------------------------------------------------------------
# Tokens. Keep in sync with brand/BRAND.md.
# ---------------------------------------------------------------------------
INK = "#0E0F11"        # primary dark
GRAPHITE = "#1F2125"   # raised surface on dark
STONE = "#6B6F76"      # secondary text on light
ASH = "#9EA2A9"        # secondary text on dark
RULE_LIGHT = "#E3E2DE"
RULE_DARK = "#26282C"
PAPER = "#F6F5F2"      # primary light (warm off-white)
SIGNAL = "#E5482D"     # the one accent; used sparingly

THEMES = {
    "light": dict(bg=PAPER, fg=INK, muted=STONE, rule=RULE_LIGHT),
    "dark": dict(bg=INK, fg=PAPER, muted=ASH, rule=RULE_DARK),
}

SANS = ("schibsted-grotesk", 600)
SANS_MED = ("schibsted-grotesk", 500)
MONO = ("ibm-plex-mono", 400)

WORDMARK_TRACK = -0.02
HEADLINE_TRACK = -0.028

# ---------------------------------------------------------------------------
# Fonts: load Fontsource woff2 files, decompress once to a TTF cache.
# ---------------------------------------------------------------------------
_fonts: dict = {}


def _font(spec):
    if spec in _fonts:
        return _fonts[spec]
    family, weight = spec
    ttf = CACHE / f"{family}-{weight}.ttf"
    if not ttf.exists():
        src = FONTSOURCE / family / "files" / f"{family}-latin-{weight}-normal.woff2"
        if not src.exists():
            raise SystemExit(f"Missing {src}. Run the npm install from this file's docstring.")
        f = TTFont(str(src))
        f.flavor = None
        f.save(str(ttf))
    tt = TTFont(str(ttf))
    face = hb.Face(hb.Blob.from_file_path(str(ttf)))
    _fonts[spec] = (hb.Font(face), tt, tt.getGlyphSet(), face.upem)
    return _fonts[spec]


def _fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def outline(text, spec, size, x, y, track=0.0, anchor="start"):
    """Shape `text` and return (path data, width). y is the baseline."""
    font, tt, gs, upem = _font(spec)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "calt": True})
    k = size / upem
    t = track * upem
    adv = [p.x_advance + t for p in buf.glyph_positions]
    width = (sum(adv) - t) * k
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    order = tt.getGlyphOrder()
    out, pen_x = [], 0.0
    for info, pos, a in zip(buf.glyph_infos, buf.glyph_positions, adv):
        pen = SVGPathPen(gs, ntos=_fmt)
        gx = x + (pen_x + pos.x_offset) * k
        gs[order[info.codepoint]].draw(TransformPen(pen, (k, 0, 0, -k, gx, y - pos.y_offset * k)))
        if pen.getCommands():
            out.append(pen.getCommands())
        pen_x += a
    return " ".join(out), width


def text(s, spec, size, x, y, fill, track=0.0, anchor="start"):
    d, w = outline(s, spec, size, x, y, track, anchor)
    return f'<path fill="{fill}" d="{d}"/>', w


def ascender(spec, size):
    """Height of a lowercase ascender ('l') above the baseline at `size`."""
    _, tt, gs, upem = _font(spec)
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(gs)
    gs[tt.getBestCmap()[ord("l")]].draw(bp)
    return bp.bounds[3] * size / upem


# ---------------------------------------------------------------------------
# The mark: a lowercase b in two parts.
# The stem is the structure (build), the bowl is the running system (runtime);
# the gap between them is the interface. Drawn on a 64 x 64 grid.
# ---------------------------------------------------------------------------
STROKE = 10
GAP = 5
STEM_X, STEM_TOP, BASE = 12, 8, 56
BOWL_TOP, BOWL_RIGHT = 24, 52
OVERSHOOT = 0.75   # optical: round forms dip slightly below the baseline
MARK_BOX = (STEM_X, STEM_TOP, BOWL_RIGHT - STEM_X, BASE - STEM_TOP)  # x, y, w, h


def _bowl(L, X, T, B, s):
    R = (B - T) / 2
    r = R - s
    return (f"M{L} {T}H{X-R}A{R} {R} 0 0 1 {X} {T+R}A{R} {R} 0 0 1 {X-R} {B}H{L}V{B-s}"
            f"H{X-s-r}A{r} {r} 0 0 0 {X-s} {T+R}A{r} {r} 0 0 0 {X-s-r} {T+s}H{L}Z")


MARK_PATH = (
    f"M{STEM_X} {STEM_TOP}h{STROKE}v{BASE-STEM_TOP}h-{STROKE}Z "
    + _bowl(STEM_X + STROKE + GAP, BOWL_RIGHT, BOWL_TOP - OVERSHOOT, BASE + OVERSHOOT, STROKE)
)


def mark(x, y, height, fill):
    """Place the mark so its visible box (not the 64 grid) starts at x, y."""
    k = height / MARK_BOX[3]
    tx, ty = x - MARK_BOX[0] * k, y - MARK_BOX[1] * k
    return (f'<path fill="{fill}" transform="translate({_fmt(tx)} {_fmt(ty)}) scale({_fmt(k)})" '
            f'd="{MARK_PATH}"/>')


def mark_width(height):
    return MARK_BOX[2] * height / MARK_BOX[3]


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------
def svg(w, h, body, title, desc=""):
    d = f"<desc>{desc}</desc>" if desc else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t"><title id="t">{title}</title>{d}{body}</svg>\n')


def panel(t, w, h):
    return (f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" fill="none" stroke="{t["rule"]}"/>')


def lockup(x, baseline, size, fg):
    """Mark + wordmark. Mark height = ascender height; both sit on the baseline."""
    asc = ascender(SANS, size)
    m = mark(x, baseline - asc, asc, fg)
    gap = asc * 0.42
    wm, w = text("buildruntime", SANS, size, x + mark_width(asc) + gap, baseline, fg, WORDMARK_TRACK)
    return m + wm, mark_width(asc) + gap + w, asc


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
def build_marks():
    tile = (f'<rect width="64" height="64" rx="14" fill="{INK}"/>'
            f'<g transform="translate(32 32) scale(.78) translate(-32 -32)"><path fill="{PAPER}" d="{MARK_PATH}"/></g>')
    (OUT / "logo-mark.svg").write_text(svg(64, 64, tile, "Buildruntime"))
    for name, fill in (("on-light", INK), ("on-dark", PAPER)):
        (OUT / f"logo-mark-{name}.svg").write_text(
            svg(64, 64, f'<path fill="{fill}" d="{MARK_PATH}"/>', "Buildruntime"))


def build_lockups():
    size = 48
    for theme, fg in (("light", INK), ("dark", PAPER)):
        body, w, asc = lockup(1, 52, size, fg)
        (OUT / f"logo-horizontal-{theme}.svg").write_text(
            svg(round(w + 2), 64, body, "Buildruntime"))
        wm, w = text("buildruntime", SANS, size, 0, 52, fg, WORDMARK_TRACK)
        (OUT / f"wordmark-{theme}.svg").write_text(svg(round(w + 1), 64, wm, "Buildruntime"))


HEAD_1 = "Software engineering,"
HEAD_2 = "from build to runtime."


def _hero(t, W, H, pad, lock_size, head_size, lead):
    b = [panel(t, W, H)]
    body, _, asc = lockup(pad, pad + 30, lock_size, t["fg"])
    b.append(body)
    base2 = H - pad - head_size * 0.08
    base1 = base2 - head_size * lead
    l1, _ = text(HEAD_1, SANS_MED, head_size, pad - head_size * 0.04, base1, t["fg"], HEADLINE_TRACK)
    l2, _ = text(HEAD_2, SANS_MED, head_size, pad - head_size * 0.04, base2, t["muted"], HEADLINE_TRACK)
    b += [l1, l2]
    return "".join(b)


def build_banners():
    W, H = 1280, 520
    for theme in ("light", "dark"):
        body = _hero(THEMES[theme], W, H, pad=80, lock_size=34, head_size=92, lead=1.06)
        (OUT / f"banner-{theme}.svg").write_text(svg(
            W, H, body, "Buildruntime: software engineering, from build to runtime",
            "The Buildruntime logo above the line 'Software engineering, from build to runtime.'"))


def build_social():
    W, H = 1280, 640
    body = _hero(THEMES["dark"], W, H, pad=96, lock_size=40, head_size=104, lead=1.06)
    (OUT / "social-preview.svg").write_text(svg(
        W, H, body, "Buildruntime: software engineering, from build to runtime"))


def build_avatar():
    S = 512
    h = 232
    w = mark_width(h)
    # optical centre: the bowl carries more weight than the stem, nudge left
    body = f'<rect width="{S}" height="{S}" fill="{INK}"/>' + mark((S - w) / 2 - 4, (S - h) / 2, h, PAPER)
    (OUT / "avatar.svg").write_text(svg(S, S, body, "Buildruntime"))


PALETTE = [
    ("Ink", INK, PAPER), ("Graphite", GRAPHITE, PAPER), ("Stone", STONE, PAPER),
    ("Ash", ASH, INK), ("Paper", PAPER, INK), ("Signal", SIGNAL, PAPER),
]


def build_palette():
    W, H = 1280, 200
    n, gap = len(PALETTE), 12
    sw = (W - gap * (n - 1)) / n
    b = []
    for i, (name, hexv, ink) in enumerate(PALETTE):
        x = i * (sw + gap)
        b.append(f'<rect x="{x:.1f}" y=".5" width="{sw:.1f}" height="{H-1}" fill="{hexv}" '
                 f'stroke="{RULE_LIGHT}"/>')
        el, _ = text(name, SANS_MED, 22, x + 20, H - 48, ink)
        b.append(el)
        el, _ = text(hexv, MONO, 16, x + 20, H - 22, ink)
        b.append(f'<g opacity=".72">{el}</g>')
    (OUT / "palette.svg").write_text(svg(W, H, "".join(b), "Buildruntime colour palette"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_marks()
    build_lockups()
    build_banners()
    build_social()
    build_avatar()
    build_palette()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    main()
