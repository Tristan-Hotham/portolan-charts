// QA: renders the page against local test tiles (OpenFreeMap and Terrarium tiles saved for The Inked World), records
// console errors, screenshots and a few interactions. Usage: node code/qa.js  (needs a file server at http://localhost:8765/
// serving the file system root, playwright, and maplibre-gl 4.7.1 in MAPLIBRE_DIST)
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const ML = process.env.MAPLIBRE_DIST || '/tmp/ml/node_modules/maplibre-gl/dist';
const ROOT = path.join(__dirname, '..');
const BASE = 'http://localhost:8765' + ROOT + '/index.html';
const TJ = process.env.TJ || 'http://localhost:8765/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/tj_local.json';
const DEM = 'http://localhost:8765/home/claude/newdata/raw9/terrarium/{z}/{x}/{y}.png';
const shots = [
  { out: 'desk_pisana', w: 1280, h: 860 },
  { out: 'desk_pisana_morph', w: 1280, h: 860, q: { morph: 100, arrows: 1 } },
  { out: 'desk_catalan_sel', w: 1280, h: 860, q: { chart: 'catalan', sel: 'c050' } },
  { out: 'phone_pisana', w: 390, h: 844, dpr: 2 },
  { out: 'phone_catalan_sel', w: 390, h: 844, dpr: 2, q: { chart: 'catalan', sel: 'c020' } },
  { out: 'page_full', w: 1280, h: 860, full: true },
  { out: 'phone_full', w: 390, h: 844, full: true },
];
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const errors = [], info = {};
  fs.mkdirSync(path.join(ROOT, 'qa'), { recursive: true });
  for (const s of shots.filter(s => !ONLY || ONLY.includes(s.out))) {
    const ctx = await browser.newContext({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: s.dpr || 1 });
    const page = await ctx.newPage();
    await page.route(/cdn\.jsdelivr\.net\/npm\/maplibre-gl@4\.7\.1\/dist\/(.*)/, (route, req) => {
      const f = path.join(ML, req.url().split('/dist/')[1]);
      route.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' });
    });
    await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
    page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource|net::ERR/.test(m.text())) errors.push(`[${s.out}] ${m.text().slice(0, 200)} ${(m.location() || {}).url || ''}`); });
    page.on('pageerror', e => errors.push(`[${s.out}] pageerror: ${e.message}`));
    const q = new URLSearchParams({ tj: TJ, dem: DEM, demmax: '12', ...(s.q || {}) });
    await page.goto(`${BASE}?${q}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__chart && window.__world, null, { timeout: 90000 });
    const idle = () => page.evaluate(() => Promise.all([window.__chart, window.__world].map(m => new Promise(res => { m.once('idle', () => setTimeout(res, 600)); m.triggerRepaint(); setTimeout(res, 30000); }))));
    await idle(); await page.waitForTimeout(1500); await idle();
    info[s.out] = await page.evaluate(() => ({ scrollW: document.documentElement.scrollWidth, fsBtns: document.querySelectorAll('.mfs-btn').length,
      pts: window.__chart.queryRenderedFeatures({ layers: ['pts'] }).length, wpts: window.__world.getLayer('wpts') ? window.__world.queryRenderedFeatures({ layers: ['wpts'] }).length : -1,
      popup: (document.querySelector('.maplibregl-popup-content') || {}).innerText || null, stat: document.getElementById('stat').textContent }));
    await page.screenshot({ path: path.join(ROOT, 'qa', s.out + '.png'), fullPage: !!s.full, timeout: 120000 });
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(ROOT, 'qa', 'qa.json'), JSON.stringify({ errors, info }, null, 1));
  console.log(JSON.stringify({ errors, info }, null, 1));
})();
