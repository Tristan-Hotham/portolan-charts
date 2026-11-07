/* How accurate were portolan charts? The page's two maps: the chart itself (deep zoom, with the distortion grid, the
 * true coast morphing onto the drawing, and every point I read) and The Inked World showing where each place really is.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const BASE = window.INKBASE;
  const V = '?v=20261107';
  const ENGINE = ['js/curated.js', 'js/ink-palette.js', 'js/ink-icons.js', 'js/ink-houses.js', 'js/ink-map.js', 'js/ink-extras.js'];
  const CONF = { 1: 'clear name, certain place', 2: 'probable', 3: 'place certain, exact point or reading doubtful' };
  const SRC = { s: 'read on the scan', f: 'read on Jomard\'s facsimile and carried to the scan' };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  let SITE = null, CH = qs.get('chart') === 'catalan' ? 'catalan' : 'pisana', T = 0, chart = null, world = null, sel = null;
  const pops = { chart: null, world: null };

  // page theme (the maps stay parchment)
  document.getElementById('theme').addEventListener('click', () => {
    const r = document.documentElement, dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    r.dataset.theme = dark ? 'light' : 'dark';
  });
  const ct = document.getElementById('cartouche');
  const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function loadScripts(list) {
    return list.reduce((p, src) => p.then(() => new Promise((res, rej) => {
      const el = document.createElement('script'); el.src = BASE + src + V; el.onload = res; el.onerror = () => rej(new Error('script ' + src)); document.head.appendChild(el);
    })), Promise.resolve());
  }

  // ---------------- pen-drawn marks: a wobbly inked ring with a dot, in the basin's ink
  function penRing(col, r, sel) {
    const k = 2, s = Math.ceil((r * 2 + 8) * k), c = document.createElement('canvas'); c.width = c.height = s;
    const x = c.getContext('2d'); x.scale(k, k); const m = s / k / 2;
    x.lineCap = 'round'; x.strokeStyle = '#2B2119'; x.lineWidth = sel ? 2.4 : 1.5;
    x.fillStyle = sel ? 'rgba(251,245,228,0.95)' : 'rgba(251,245,228,0.85)';
    x.beginPath();
    for (let i = 0; i <= 40; i++) { const a = i / 40 * Math.PI * 2 + 0.3, rr = r * (1 + 0.06 * Math.sin(a * 3 + 1) + (i > 37 ? 0.08 : 0)); x.lineTo(m + rr * Math.cos(a), m + rr * Math.sin(a)); }
    x.fill(); x.stroke();
    x.fillStyle = col; x.beginPath(); x.arc(m, m, r * 0.48, 0, Math.PI * 2); x.fill();
    if (sel) { x.strokeStyle = '#A3261B'; x.lineWidth = 1.6; x.beginPath(); x.arc(m, m, r + 3.2, 0, Math.PI * 2); x.stroke(); }
    return { width: s, height: s, data: new Uint8Array(x.getImageData(0, 0, s, s).data.buffer) };
  }
  function addIcons(map) {
    SITE.basins.forEach(([n, c], i) => {
      if (!map.hasImage('pt' + i)) map.addImage('pt' + i, penRing(c, 5.5, false), { pixelRatio: 2 });
      if (!map.hasImage('ps' + i)) map.addImage('ps' + i, penRing(c, 7, true), { pixelRatio: 2 });
    });
  }

  // ---------------- data in GeoJSON
  const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  function fc(features) { return { type: 'FeatureCollection', features }; }
  function line(cs, p) { return { type: 'Feature', properties: p || {}, geometry: { type: 'LineString', coordinates: cs } }; }
  function chartPoints() {
    const C = SITE.charts[CH];
    return fc(C.points.map(p => ({ type: 'Feature', id: +p.id.slice(1), properties: { id: p.id, l: p.l, n: p.n, b: p.b, ic: (sel === p.id ? 'ps' : 'pt') + p.b },
      geometry: { type: 'Point', coordinates: lerp(p.p, p.q, T) } })));
  }
  function morphLines(a, b) { return a.map((L, i) => L.map((v, j) => lerp(v, b[i][j], T))); }
  function setChartData() {
    const C = SITE.charts[CH];
    chart.getSource('pts').setData(chartPoints());
    chart.getSource('coast').setData(fc(morphLines(C.coast_tps, C.coast_sim).map(c => line(c))));
    chart.getSource('arrows').setData(fc(C.points.map(p => line([p.p, p.q], { id: p.id }))));
    chart.getSource('gt').setData(fc(morphLines(C.grid_tps, C.grid_sim).map(c => line(c))));
    chart.setPaintProperty('img', 'raster-opacity', 1 - 0.72 * T);
  }
  function worldData() {
    const C = SITE.charts[CH];
    world.getSource('wpts').setData(fc(C.points.map(p => ({ type: 'Feature', properties: { id: p.id, n: p.n, b: p.b, ic: (sel === p.id ? 'ps' : 'pt') + p.b }, geometry: { type: 'Point', coordinates: p.t } }))));
    world.getSource('werr').setData(fc(C.points.map(p => line([p.t, p.f], { id: p.id, b: p.b }))));
  }

  // ---------------- the chart viewer
  function chartStyle(C) {
    return {
      version: 8, glyphs: BASE + 'fonts/{fontstack}/{range}.pbf',
      sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#EEE6D2' } }]
    };
  }
  function buildChart(C) {
    const b = C.bounds;
    chart.addSource('img', { type: 'raster', tiles: [new URL('img/', location.href).href + `tiles_${CH}/{z}/{x}/{y}.webp`], tileSize: 256, minzoom: 1, maxzoom: C.tz, bounds: [b[0][0], b[0][1], b[1][0], b[1][1]],
      attribution: CH === 'pisana' ? 'Carta Pisana, BnF GE B-1118 (Wikimedia Commons, public domain)' : 'Catalan Atlas, BnF Espagnol 30 (Wikimedia Commons, public domain)' });
    chart.addLayer({ id: 'img', type: 'raster', source: 'img', paint: { 'raster-fade-duration': 0 } });
    chart.addSource('gt', { type: 'geojson', data: fc(C.grid_tps.map(c => line(c))) });
    chart.addSource('gs', { type: 'geojson', data: fc(C.grid_sim.map(c => line(c))) });
    chart.addSource('gl', { type: 'geojson', data: fc(C.grid_lab.map(([x, y, t]) => ({ type: 'Feature', properties: { t }, geometry: { type: 'Point', coordinates: [x, y] } }))) });
    chart.addSource('coast', { type: 'geojson', data: fc([]) });
    chart.addSource('arrows', { type: 'geojson', data: fc([]) });
    chart.addSource('pts', { type: 'geojson', data: fc([]) });
    chart.addLayer({ id: 'gs', type: 'line', source: 'gs', layout: { visibility: 'none' }, paint: { 'line-color': '#3D6E9E', 'line-width': 1.3, 'line-dasharray': [4, 3], 'line-opacity': 0.85 } });
    chart.addLayer({ id: 'gt', type: 'line', source: 'gt', paint: { 'line-color': '#A3261B', 'line-width': ['interpolate', ['linear'], ['zoom'], 1, 1, 6, 2.2], 'line-opacity': 0.85 } });
    chart.addLayer({ id: 'gl', type: 'symbol', source: 'gl', minzoom: CH === 'pisana' ? 2.5 : 3.5, layout: { 'text-field': ['get', 't'], 'text-font': ['Ink Italic'], 'text-size': 12, 'text-offset': [0, -0.7] },
      paint: { 'text-color': '#A3261B', 'text-halo-color': 'rgba(251,245,228,0.9)', 'text-halo-width': 1.4 } });
    chart.addLayer({ id: 'coast', type: 'line', source: 'coast', paint: { 'line-color': '#2B2119', 'line-width': ['interpolate', ['linear'], ['zoom'], 1, 0.9, 6, 2], 'line-opacity': 0.8 } });
    chart.addLayer({ id: 'arrows', type: 'line', source: 'arrows', layout: { visibility: 'none' }, paint: { 'line-color': '#A3261B', 'line-width': 1.6, 'line-dasharray': [2, 1.5] } });
    chart.addLayer({ id: 'pts', type: 'symbol', source: 'pts', layout: { 'icon-image': ['get', 'ic'], 'icon-allow-overlap': true, 'icon-size': ['interpolate', ['linear'], ['zoom'], 1, 0.7, 5, 1.1] } });
    chart.addLayer({ id: 'ptl', type: 'symbol', source: 'pts', minzoom: CH === 'pisana' ? 3.2 : 4.3, layout: { 'text-field': ['get', 'l'], 'text-font': ['Ink Italic'], 'text-size': 12.5,
      'text-offset': [0, 1.0], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': 'rgba(251,245,228,0.92)', 'text-halo-width': 1.5 } });
    setChartData(); applyChartLayers();
  }
  function switchChart(ch) {
    CH = ch; sel = null; closePops();
    for (const id of ['ptl', 'pts', 'arrows', 'coast', 'gl', 'gt', 'gs', 'img']) if (chart.getLayer(id)) chart.removeLayer(id);
    for (const id of ['pts', 'arrows', 'coast', 'gl', 'gt', 'gs', 'img']) if (chart.getSource(id)) chart.removeSource(id);
    const C = SITE.charts[CH];
    buildChart(C);
    chart.fitBounds(C.bounds, { padding: 10, duration: 0 });
    if (world) { worldData(); world.fitBounds(small ? [[-10, 30], [42, 50]] : [[-18, 27], [44, 58]], { padding: 10, duration: 800 }); }
    document.querySelectorAll('#chartChips .chip').forEach(b => b.setAttribute('aria-pressed', b.dataset.c === CH));
    document.getElementById('stat').innerHTML = `${esc(C.name)} (${esc(C.date)}): ${C.points.length} places read · turned <b>${C.rot}°</b> anticlockwise · median miss ${C.median} km, ${C.local} km against its neighbours`;
    const u = new URL(location.href); u.searchParams.set('chart', CH); history.replaceState(null, '', u);
  }
  function applyChartLayers() {
    const vis = (id, on) => chart.getLayer(id) && chart.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
    const c = id => document.getElementById(id).checked;
    vis('img', c('lyImg')); vis('gt', c('lyGrid')); vis('gl', c('lyGrid')); vis('gs', c('lyFit')); vis('coast', c('lyCoast'));
    vis('pts', c('lyPts')); vis('ptl', c('lyPts') && c('lyNames')); vis('arrows', c('lyArr'));
  }

  // ---------------- popups, kept in step on both maps
  function closePops() { for (const k in pops) if (pops[k]) { pops[k].remove(); pops[k] = null; } }
  function html(p) {
    const B = SITE.basins[p.b][0], C = SITE.charts[CH];
    return `<b class="t">${esc(p.l)}</b><div>${esc(p.n)}</div><table>
      <tr><td>Chart</td><td>${esc(C.name)}${p.sh ? ', sheet ' + p.sh : ''}</td></tr>
      <tr><td>Sea</td><td>${esc(B)}</td></tr>
      <tr><td>Best-fit miss</td><td>${p.e} km</td></tr>
      <tr><td>Against its 8 neighbours</td><td>${p.o} km</td></tr>
      <tr><td>Reading</td><td>${esc(CONF[p.c])}</td></tr>
      <tr><td>Source</td><td>${esc(SRC[p.s] || '')}</td></tr></table>
      <p class="nt">True position ${p.t[1].toFixed(2)}° N, ${Math.abs(p.t[0]).toFixed(2)}° ${p.t[0] < 0 ? 'W' : 'E'}. Names in brackets are features I read from the drawn coast, not a written name.</p>`;
  }
  function select(id, fly) {
    const C = SITE.charts[CH], p = C.points.find(q => q.id === id); if (!p) return;
    sel = id; fold(true); setChartData(); if (world) worldData(); closePops();
    const pos = lerp(p.p, p.q, T);
    pops.chart = new maplibregl.Popup({ maxWidth: '300px', offset: 12 }).setLngLat(pos).setHTML(html(p)).addTo(chart);
    if (world) pops.world = new maplibregl.Popup({ maxWidth: '260px', offset: 12, closeButton: false }).setLngLat(p.t).setHTML(`<b class="t">${esc(p.n)}</b><div>${esc(p.l)} on the ${esc(C.name)}; best-fit miss ${p.e} km</div>`).addTo(world);
    if (fly) {
      chart.flyTo({ center: pos, zoom: Math.max(chart.getZoom(), C.tz - 1.2), duration: 1400 });
      if (world) world.flyTo({ center: p.t, zoom: Math.max(world.getZoom(), 6), duration: 1400 });
    }
  }
  function clickable(map, layer) {
    map.on('click', layer, e => { const f = e.features[0]; if (f) select(f.properties.id, false); });
    map.on('mouseenter', layer, () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', layer, () => map.getCanvas().style.cursor = '');
  }

  // ---------------- search
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let items = [], k = -1;
    const show = () => {
      const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1;
      if (!v) { sug.style.display = 'none'; return; }
      items = SITE.charts[CH].points.filter(p => norm(p.n).includes(v) || norm(p.l).includes(v)).slice(0, 12);
      items.forEach((p, i) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(p.n)} <span>${esc(p.l)}</span>`;
        li.addEventListener('mousedown', e => { e.preventDefault(); pick(i); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none';
    };
    const pick = i => { const p = items[i]; if (!p) return; q.value = p.n; sug.style.display = 'none'; select(p.id, true); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => {
      const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); }
      else if (e.key === 'Escape') sug.style.display = 'none';
    });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }

  // ---------------- the modern ink map
  function setupWorld(map) {
    addIcons(map);
    map.on('styleimagemissing', e => { if (/^p[ts]\d$/.test(e.id)) addIcons(map); });
    map.addSource('werr', { type: 'geojson', data: fc([]) });
    map.addSource('wpts', { type: 'geojson', data: fc([]), attribution: 'Places: my readings and identifications' });
    map.addLayer({ id: 'werr', type: 'line', source: 'werr', layout: { visibility: 'none' }, paint: { 'line-color': '#A3261B', 'line-width': 1.4, 'line-dasharray': [2, 1.5], 'line-opacity': 0.85 } });
    map.addLayer({ id: 'wpts', type: 'symbol', source: 'wpts', layout: { 'icon-image': ['get', 'ic'], 'icon-allow-overlap': true, 'icon-size': ['interpolate', ['linear'], ['zoom'], 3, 0.75, 8, 1.15] } });
    worldData(); clickable(map, 'wpts');
    const lp = document.getElementById('wlp'), btn = document.getElementById('wlyrBtn');
    btn.addEventListener('click', () => { const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    const boxes = [...lp.querySelectorAll('input[data-g]')], modern = document.getElementById('modern');
    const base = () => {
      const m = modern.checked;
      boxes.forEach(b => { const g = b.dataset.g; const inkOnly = ['mountains', 'forests', 'biomes', 'sea', 'tint'].includes(g); try { InkMap.setGroup(map, g, b.checked && !(m && inkOnly)); } catch (e) { } });
      try { InkMap.setGroup(map, 'paper', !m); InkMap.setGroup(map, 'modern', m); InkMap.setGroup(map, 'coast', !m); if (m) InkMap.setGroup(map, 'roads', false); } catch (e) { }
    };
    boxes.forEach(b => b.addEventListener('change', base)); modern.addEventListener('change', base); base();
    const we = document.getElementById('wErr'); we.addEventListener('change', () => map.setLayoutProperty('werr', 'visibility', we.checked ? 'visible' : 'none'));
    const wp = document.getElementById('wPts'); wp.addEventListener('change', () => map.setLayoutProperty('wpts', 'visibility', wp.checked ? 'visible' : 'none'));
  }

  // ---------------- start
  const dataP = fetch('data/site.json').then(r => r.json()).then(j => { SITE = j; return j; });
  dataP.then(() => {
    const C = SITE.charts[CH];
    chart = new maplibregl.Map({ container: 'chart', style: chartStyle(C), bounds: C.bounds, fitBoundsOptions: { padding: 10 }, maxZoom: C.tz + 2.2, renderWorldCopies: false,
      attributionControl: { compact: true }, dragRotate: false, pitchWithRotate: false });
    window.__chart = chart;
    chart.touchZoomRotate.disableRotation();
    chart.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    chart.on('load', () => {
      document.getElementById('nojsC').remove();
      addIcons(chart); chart.on('styleimagemissing', e => { if (/^p[ts]\d$/.test(e.id)) addIcons(chart); });
      switchChart(CH); clickable(chart, 'pts'); setupSearch();
      ['lyImg', 'lyGrid', 'lyFit', 'lyCoast', 'lyPts', 'lyNames', 'lyArr'].forEach(id => document.getElementById(id).addEventListener('change', applyChartLayers));
      const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
      btn.addEventListener('click', () => { const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
      document.querySelectorAll('#chartChips .chip').forEach(b => b.addEventListener('click', () => { if (b.dataset.c !== CH) switchChart(b.dataset.c); }));
      const r = document.getElementById('morph'), lab = document.getElementById('morphLab');
      const set = v => { T = v / 100; lab.textContent = T < 0.02 ? 'As drawn' : T > 0.98 ? 'True coast' : Math.round(T * 100) + '%'; setChartData();
        if (sel && pops.chart) { const p = SITE.charts[CH].points.find(q => q.id === sel); pops.chart.setLngLat(lerp(p.p, p.q, T)); } };
      r.addEventListener('input', () => set(+r.value));
      if (qs.get('morph')) { r.value = qs.get('morph'); set(+r.value); }
      if (qs.get('arrows')) { document.getElementById('lyArr').checked = true; applyChartLayers(); }
      if (qs.get('sel')) select(qs.get('sel'), true);
      const first = e => { if (e.target.closest && e.target.closest('.cartouche,.ov,.lp,.morph,.mfs-btn,.maplibregl-ctrl')) return; fold(true); };
      document.getElementById('chartWrap').addEventListener('pointerdown', first, { capture: true, passive: true, once: true });
    });
    // the world map, on The Inked World engine
    const opts = { base: BASE, winter: false };
    if (qs.get('tj')) opts.tilejson = qs.get('tj');
    if (qs.get('dem')) opts.dem = qs.get('dem');
    if (qs.get('demmax')) opts.demMax = +qs.get('demmax');
    opts.mapOptions = { bounds: small ? [[-10, 30], [42, 50]] : [[-18, 27], [44, 58]], fitBoundsOptions: { padding: 10 } };
    return loadScripts(ENGINE).then(() => InkMap.create('map', opts)).then(map => {
      map.__inkWinter = false; world = map; window.__world = map;
      const n = document.getElementById('nojsW'); if (n) n.remove();
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
      // the attribution starts folded (the (i) button opens it)
      const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
      map.once('idle', foldAt); map.on('resize', () => setTimeout(foldAt, 50)); foldAt(); setTimeout(foldAt, 1500);
      setupWorld(map);
      if (sel) select(sel, false);
    });
  }).catch(e => { console.error(e); for (const id of ['nojsC', 'nojsW']) { const n = document.getElementById(id); if (n) n.textContent = 'The map could not load: ' + e.message; } });
})();
