// Render every frame of scenes/index.html (driven by build/timeline.json) into build/video.mp4.
// Usage: node tools/render.mjs [--stills t1,t2,...]   (stills go to out/stills/)
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { openScene, ROOT } from './serve.mjs';

const { page, timeline, close } = await openScene(chromium);
const stillsArg = process.argv.indexOf('--stills');

if (stillsArg > 0) {
  const dir = join(ROOT, 'out', 'stills');
  await mkdir(dir, { recursive: true });
  for (const t of process.argv[stillsArg + 1].split(',').map(Number)) {
    await page.evaluate(t => renderAt(t), t);
    await page.screenshot({ path: join(dir, `t${t.toFixed(1).padStart(5, '0')}.png`) });
  }
  await close();
  process.exit(0);
}

const { fps, duration } = timeline;
const frames = Math.ceil(duration * fps);
await mkdir(join(ROOT, 'build'), { recursive: true });
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', join(ROOT, 'build', 'video.mp4')],
  { stdio: ['pipe', 'inherit', 'inherit'] });
const done = new Promise((ok, fail) => ff.on('close', c => (c ? fail(new Error(`ffmpeg exited ${c}`)) : ok())));

const t0 = Date.now();
for (let f = 0; f < frames; f++) {
  await page.evaluate(t => renderAt(t), f / fps);
  const jpg = await page.screenshot({ type: 'jpeg', quality: 95 });
  if (!ff.stdin.write(jpg)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % (fps * 10) === 0) console.log(`frame ${f}/${frames}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
ff.stdin.end();
await done;
await close();
console.log(`rendered ${frames} frames → build/video.mp4`);
