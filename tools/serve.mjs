// Minimal static server for the repo root, so the scene page can load fonts and the timeline.
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = normalize(join(fileURLToPath(import.meta.url), '..', '..'));
const TYPES = { '.html': 'text/html', '.json': 'application/json', '.woff2': 'font/woff2', '.js': 'text/javascript', '.png': 'image/png' };

export function serve() {
  const server = createServer(async (req, res) => {
    const path = normalize(join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname)));
    if (!path.startsWith(ROOT)) { res.writeHead(403).end(); return; }
    try {
      const body = await readFile(path);
      res.writeHead(200, { 'content-type': TYPES[extname(path)] || 'application/octet-stream' }).end(body);
    } catch { res.writeHead(404).end(); }
  });
  return new Promise(ok => server.listen(0, '127.0.0.1', () => ok({ server, url: `http://127.0.0.1:${server.address().port}` })));
}

export async function openScene(chromium) {
  const { server, url } = await serve();
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => { throw e; });
  await page.goto(`${url}/scenes/index.html`);
  const timeline = await page.evaluate(() => window.ready);
  // Sound-design cues are defined next to the animation they belong to; export them for tools/music.py.
  const cues = await page.evaluate(() => (window.cues ? window.cues() : { cues: [], quiet: [] }));
  await writeFile(join(ROOT, 'build', 'cues.json'), JSON.stringify(cues, null, 2));
  return { page, timeline, close: async () => { await browser.close(); server.close(); } };
}
