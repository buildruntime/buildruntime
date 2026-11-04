# Buildruntime brand guidelines

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/brand/logo-horizontal-dark.svg">
  <img alt="Buildruntime" src="../assets/brand/logo-horizontal-light.svg" height="48">
</picture>

This document is the reference for how Buildruntime looks and sounds. Every asset in
[`assets/brand/`](../assets/brand) is generated from [`generate.py`](generate.py), so
change the tokens there and regenerate rather than editing SVGs by hand.

## 1. Name

- Written **Buildruntime** in prose: one word, capital B only.
- Written **buildruntime** (all lowercase) in the wordmark, CLI names, URLs and package names.
- Never "BuildRuntime", "Build Runtime" or "BR".

## 2. Tagline

> **from build to runtime**

Set in lowercase JetBrains Mono, usually followed by the orange cursor block.
Supporting line for longer copy: *Developer tooling for everything between `git push` and a healthy process in production.*

## 3. Logo

### The mark

<img src="../assets/brand/logo-mark.svg" width="72" alt="Buildruntime mark">&nbsp;&nbsp;
<img src="../assets/brand/logo-mark-on-light.svg" width="72" alt="Mark on light">&nbsp;&nbsp;
<img src="../assets/brand/avatar.svg" width="72" alt="Avatar">

A **stepped chevron** made of three blocks. The blocks are build stages and the
forward offset of the middle block is execution: the thing moving from *build* to *run*.
The middle block is always **Signal** orange. It is the only coloured element in the mark.

- Construction grid: 64 × 64. Blocks are 9 units tall, 4 units apart, 2-unit corner radius.
- Tile corner radius: 14 units (22%).
- Clear space: at least the height of one block (9/64 of the mark) on every side.
- Minimum size: 16 px for the mark, 96 px wide for the horizontal lockup.

### Lockups

| File | Use |
| --- | --- |
| `logo-mark.svg` | Primary mark on its ink tile. Use on any background. |
| `logo-mark-on-light.svg` / `logo-mark-on-dark.svg` | Mark without tile, for when the tile would be too heavy. |
| `logo-mark-mono-black.svg` / `logo-mark-mono-white.svg` | Single-colour reproduction (print, embossing, favicons on coloured UI). |
| `logo-horizontal-light.svg` / `logo-horizontal-dark.svg` | Tile + wordmark. Default logo for docs, READMEs and slides. |
| `wordmark-light.svg` / `wordmark-dark.svg` | Wordmark alone, where the mark already appears nearby. |
| `avatar.svg` / `avatar.png` | 512 × 512 profile picture (safe inside GitHub's circular crop). |
| `social-preview.svg` / `social-preview.png` | 1280 × 640 repository social preview. |
| `banner-light.svg` / `banner-dark.svg` (+ `@2x` PNGs) | README header. |
| `divider-light.svg` / `divider-dark.svg` | Optional section rule for long READMEs. |

### Don't

- Recolour the outer blocks or make the core block anything but Signal orange.
- Rotate, skew, outline or add effects (shadows, glows, gradients) to the mark.
- Re-type the wordmark in a live font. Use the outlined SVGs.
- Place the mark-without-tile on mid-tone or busy backgrounds; use the tile version instead.

## 4. Colour

<img src="../assets/brand/palette.svg" alt="Buildruntime colour palette" width="100%">

| Token | Hex | Role |
| --- | --- | --- |
| Ink 950 | `#0B0F17` | Primary dark. Tile, dark backgrounds, text on light. |
| Ink 900 | `#121826` | Raised surfaces on dark. |
| Ink 800 | `#1B2232` | Grid dots and hairlines on dark. |
| Ink 700 | `#283043` | Borders and inactive rails on dark. |
| Slate 500 | `#5B6474` | Secondary text on light. |
| Slate 400 | `#8A94A6` | Secondary text on dark. |
| Line | `#DCE1E8` | Borders and grid on light. |
| Paper | `#F7F8FA` | Light backgrounds, text on dark. |
| **Signal** | `#FF5B2E` | Primary accent: the core block, progress, calls to action. |
| Signal Soft | `#FF8A5C` | Hover / secondary accent. |
| **Run** | `#2BD99F` | Status accent: "live", "passing", "running". Use sparingly. |

Proportion: roughly 70% Ink/Paper, 25% Slate/Line, 5% Signal + Run together.
Contrast: Signal on Ink 950 is about 6.2:1 (fine for text). Signal on Paper is only
about 2.9:1, so on light backgrounds use it for fills, icons and the mark, never for text.

## 5. Typography

| Role | Typeface | Notes |
| --- | --- | --- |
| Wordmark, headlines | **Inter Display Bold** | Tracking −3.5% at display sizes. |
| UI and body | **Inter** Regular / Medium | Default tracking. |
| Code, tagline, labels | **JetBrains Mono** Medium | Lowercase for the tagline and stage labels. |

Both families are licensed under the SIL Open Font License 1.1 and are free to use.

## 6. Graphic motif: the pipeline rail

The rail `build → test → package → deploy → run` appears on banners and previews.
Completed stages are Signal-outlined squares on a Signal line; the final **run**
stage is a Run-green dot with a soft halo. Keep the stage names lowercase and in mono.

## 7. Voice

- **Plain and specific.** Say what a tool does and how fast, not that it is "revolutionary".
- **Engineer to engineer.** Assume the reader is technical; skip the hype.
- **Calm.** Builds and deploys are stressful enough. Our copy should not add to it.

## 8. Regenerating assets

```bash
pip install fonttools uharfbuzz
python3 brand/generate.py      # SVGs
node brand/export-png.js       # PNGs (needs Playwright + Chromium)
```
