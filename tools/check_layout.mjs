// Frame-by-frame layout and logic validation of the scene page.
// Checks: text inside the frame safe area, text inside its card, no text overlap, captions clear of
// content and single-line, caption/narration timing, "proposed" framing, and ED → ward ordering.
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { openScene, ROOT } from './serve.mjs';

const SAFE = [48, 48, 1872, 1032], CAPTION_TOP = 930, STEP = 0.2;
const { page, timeline: TL, close } = await openScene(chromium);
const errors = [], screenText = new Set();
let arrivedAt;
const fail = (t, msg) => errors.push(`t=${t.toFixed(2)}s  ${msg}`);
const inside = (r, b, tol = 2) => r[0] >= b[0] - tol && r[1] >= b[1] - tol && r[2] <= b[2] + tol && r[3] <= b[3] + tol;
const hit = (a, b) => a[0] < b[2] - 1 && b[0] < a[2] - 1 && a[1] < b[3] - 1 && b[1] < a[3] - 1;

// Timeline-level checks.
let prevEnd = 0;
for (const s of TL.scenes) {
  if (Math.abs(s.start - prevEnd) > 1e-3) errors.push(`${s.id}: gap/overlap with previous scene`);
  prevEnd = s.end;
  for (const l of s.lines) {
    if (l.start < s.start || l.end > s.end - .3) errors.push(`${s.id}: narration "${l.text.slice(0, 40)}…" spills outside its scene`);
    for (const c of l.captions) if (c.start < l.start - 1e-3 || c.end > l.end + 1e-3) errors.push(`${s.id}: caption outside its narration line`);
  }
}

for (let t = 0; t <= TL.duration; t += STEP) {
  await page.evaluate(t => renderAt(t), t);
  const f = await page.evaluate(() => inspectFrame());
  const solid = f.items.filter(i => i.opacity > .6);
  for (const it of f.items) {
    if (it.opacity > .3) screenText.add(it.text);
    for (const r of it.rects) {
      if (!inside(r, SAFE)) fail(t, `text outside safe area: "${it.text}" ${r.map(Math.round)}`);
      if (it.box && !inside(r, it.box)) fail(t, `text overflows its card ${it.boxId}: "${it.text}"`);
      if (it.opacity > .3 && r[3] > CAPTION_TOP) fail(t, `content text in caption zone: "${it.text}"`);
    }
  }
  for (let i = 0; i < solid.length; i++) for (let j = i + 1; j < solid.length; j++)
    for (const a of solid[i].rects) for (const b of solid[j].rects)
      if (hit(a, b)) fail(t, `text overlap: "${solid[i].text}" / "${solid[j].text}"`);
  if (f.caption) {
    const c = f.caption.rect;
    if (c[3] - c[1] > 80) fail(t, `caption wraps to more than one line: "${f.caption.text}"`);
    if (!inside(c, SAFE)) fail(t, `caption outside safe area`);
    if (c[1] < CAPTION_TOP) fail(t, `caption above caption zone`);
    for (const it of f.items) for (const r of it.rects) if (it.opacity > .05 && hit(r, c)) fail(t, `caption overlaps "${it.text}"`);
  }
  // Proposed framing: from scene 4 on, the PROPOSED WORKFLOW tag must be visible (except the final fade).
  const tag = await page.evaluate(() => +getComputedStyle(document.getElementById('chrome-tag')).opacity);
  const s4 = TL.scenes.find(s => s.id === 's4').start;
  if (t > s4 + 1 && t < TL.duration - 1.3 && tag < .9) fail(t, 'PROPOSED WORKFLOW tag not visible');
  // ED → ward logic: PHIS must not show the ward location before the patient is in the ward.
  const s5 = await page.evaluate(() => ({ v2: +getComputedStyle(document.getElementById('s5-v2')).opacity,
    v1: +getComputedStyle(document.getElementById('s5-v1')).opacity,
    x: parseFloat(document.getElementById('s5-pt').style.left), scene: getComputedStyle(document.getElementById('s5')).visibility }));
  if (s5.scene === 'visible' && s5.v2 > .01 && s5.x < 1410) fail(t, 'PHIS shows ward location before patient reaches ward');
  if (s5.scene === 'visible' && s5.x >= 1419) arrivedAt ??= t;
  if (s5.scene === 'visible' && s5.v1 > .5 && arrivedAt !== undefined && t - arrivedAt > .6) fail(t, 'PHIS still shows ED location well after patient reached ward');
}
await close();

await writeFile(join(ROOT, 'build', 'screen_text.json'), JSON.stringify([...screenText].sort(), null, 2));
// Group identical problems across frames: report first time seen and frame count.
const groups = new Map();
for (const e of errors) { const [, t, msg] = e.match(/^t=([\d.]+)s  (.*)$/) || [, '-', e]; const g = groups.get(msg) || { t, n: 0 }; g.n++; groups.set(msg, g); }
if (groups.size) {
  for (const [msg, g] of groups) console.log(`from t=${g.t}s (${g.n} frame${g.n > 1 ? 's' : ''})  ${msg}`);
  console.log(`\nlayout: ${groups.size} problem(s)`); process.exit(1);
}
console.log(`layout: OK (${Math.round(TL.duration / STEP)} frames sampled, ${screenText.size} on-screen strings)`);
