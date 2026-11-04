#!/usr/bin/env node
// Rasterise the brand SVGs into PNGs for places that do not accept SVG
// (GitHub avatar, repository social preview, slide decks, chat apps).
//
// Usage: node brand/export-png.js     (needs `playwright` with Chromium)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DIR = path.resolve(__dirname, '..', 'assets', 'brand');

// [source svg, output png, css width, css height, device scale]
const EXPORTS = [
  ['avatar.svg', 'avatar.png', 512, 512, 1],                // GitHub profile picture
  ['social-preview.svg', 'social-preview.png', 1280, 640, 1], // repo social preview (<1 MB)
  ['banner-dark.svg', 'banner-dark.png', 1280, 400, 2],
  ['banner-light.svg', 'banner-light.png', 1280, 400, 2],
  ['logo-mark.svg', 'logo-mark-512.png', 512, 512, 1],
  ['logo-horizontal-light.svg', 'logo-horizontal-light.png', null, 64, 4],
  ['logo-horizontal-dark.svg', 'logo-horizontal-dark.png', null, 64, 4],
];

(async () => {
  const browser = await chromium.launch();
  for (const [src, out, w0, h, scale] of EXPORTS) {
    const file = path.join(DIR, src);
    const svg = fs.readFileSync(file, 'utf8');
    const w = w0 ?? Number(svg.match(/width="([\d.]+)"/)[1]);
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
    await page.goto('file://' + file);
    await page.evaluate(() => {
      const s = document.querySelector('svg');
      s.setAttribute('width', window.innerWidth);
      s.setAttribute('height', window.innerHeight);
      document.documentElement.style.margin = '0';
    });
    await page.screenshot({ path: path.join(DIR, out), omitBackground: true });
    await page.close();
    const kb = (fs.statSync(path.join(DIR, out)).size / 1024).toFixed(1);
    console.log(`assets/brand/${out}  ${w * scale}x${h * scale}  ${kb} KB`);
  }
  await browser.close();
})();
