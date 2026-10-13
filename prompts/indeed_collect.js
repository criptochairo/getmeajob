// Plantilla: NO la pegues tal cual. Genera la versión del usuario con `gmaj collector indeed` (consultas, ubicaciones, piso y zonas de user/search.yaml).
// Se ejecuta con la herramienta de JavaScript del navegador en una pestaña de Indeed del país del usuario (sesión iniciada; si sale Cloudflare, anotarlo y seguir).
// Igual que occ_collect.js: se lanza sin await ('started'), se consulta `window.__indeed_done` (esperas ≤10 s) y se leen filas con
// `window.__indeed_page(0)`, `(1)`... (≤600 caracteres). JSON completo para `gmaj add-jobs`: `window.__indeed_json(0)`, `(1)`... (≤700 caracteres
// por trozo; concatenar tal cual hasta null) — o escribir `JSON.stringify(window.__indeed)` en el body y leer el texto de la página.
// Lee el JSON embebido en /jobs (window.mosaic.providerData). /viewjob por fetch da 403: la oferta completa se lee en el navegador antes de adaptar.
window.__indeed_done = null;
(async () => {
  const QUERIES = __QUERIES__;
  const LOCATIONS = __LOCATIONS__;
  const results = async (q, l) => {
    let r;
    for (let attempt = 0; attempt < 3; attempt++) {   // 429 tras ~28 búsquedas seguidas (2026-10-12): esperar 60/120 s y reintentar
      r = await fetch(`/jobs?q=${encodeURIComponent(q)}&l=${encodeURIComponent(l)}&fromage=3`, {credentials: 'include'});
      if (r.status !== 429) break;
      await new Promise(res => setTimeout(res, 60000 * (attempt + 1)));
    }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const h = await r.text();
    const key = 'window.mosaic.providerData["mosaic-provider-jobcards"]=';
    const i = h.indexOf(key);
    if (i < 0) throw new Error('sin mosaic (¿Cloudflare o cambio de página?)');
    const s = i + key.length;
    return JSON.parse(h.slice(s, h.indexOf(';\n', s))).metaData.mosaicProviderJobCardsModel.results || [];
  };
  const found = new Map(), errors = [];
  for (const q of QUERIES) for (const l of LOCATIONS) {
    try { for (const j of await results(q, l)) if (!found.has(j.jobkey)) found.set(j.jobkey, j); }
    catch (e) { errors.push(`${q}/${l}: ${e.message}`); }
    await new Promise(r => setTimeout(r, 3000 + Math.random() * 2000));
  }
  const strip = (s) => (s || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  const legal = new RegExp(__RELEVANT__, 'i');
  const jobs = [];
  for (const j of found.values()) {
    const remoteAttr = ((j.taxonomyAttributes || []).find(a => a.label === 'remote')?.attributes || []).map(a => a.label).join(' ');
    const mode = j.remoteLocation || /home office|desde casa|remot/i.test(remoteAttr) ? 'remote' : /h[ií]brid/i.test(remoteAttr + ' ' + j.title) ? 'hybrid' : null;
    // Muchas híbridas no traen etiqueta: entran sin modo si están en la zona del usuario y se verifican en la oferta antes de adaptar.
    const home = new RegExp(__HOME__, 'i').test(j.formattedLocation || '');
    if ((!mode && !home) || !legal.test(j.title)) continue;
    const sal = j.salarySnippet?.text || '';
    const monthly = /por mes/.test(sal) ? parseInt((sal.match(/[\d,]+/g) || []).pop()?.replace(/,/g, '') || '0') : null;
    if (monthly !== null && monthly > 0 && monthly < __FLOOR__) continue;   // tope del rango publicado bajo el piso
    jobs.push({source: 'indeed', external_id: j.jobkey, url: `https://mx.indeed.com/viewjob?jk=${j.jobkey}`, title: j.title,
               company: j.company || '', location: j.formattedLocation || '', mode,
               description: (sal ? `Sueldo: ${sal}. ` : '') + `Modalidad Indeed: ${remoteAttr || mode || 'sin dato (verificar)'}. ` + strip(j.snippet).slice(0, 700)});
  }
  window.__indeed = jobs;
  const chunk = (items, size) => { const out = []; let cur = []; for (const it of items) { if (JSON.stringify([...cur, it]).length > size && cur.length) { out.push(cur); cur = []; } cur.push(it); } if (cur.length) out.push(cur); return out; };
  const pages = chunk(jobs.map(j => [j.external_id, j.mode, j.title.slice(0, 60), j.company.slice(0, 30), j.location, (j.description.match(/Sueldo: ([^.]*)/) || [, 's/d'])[1]]), 600);
  const full = JSON.stringify(jobs), parts = [];
  for (let k = 0; k < full.length; k += 700) parts.push(full.slice(k, k + 700));
  window.__indeed_page = (n) => JSON.stringify(pages[n] || null);
  window.__indeed_json = (n) => parts[n] ?? null;
  window.__indeed_done = {searched: found.size, kept: jobs.length, pages: pages.length, json_parts: parts.length, errors: errors.slice(0, 5)};
})(); 'started'
