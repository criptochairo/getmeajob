// Plantilla: NO la pegues tal cual. Genera la versión del usuario con `gmaj collector occ` (consultas, piso y palabras de user/search.yaml).
// Se ejecuta con la herramienta de JavaScript del navegador en una pestaña de occ.com.mx con la sesión del usuario iniciada.
// Corre ~2-3 min y la salida de JS se trunca (~800 caracteres): se lanza sin await ('started'), se espera consultando
// `window.__occ_done` y se leen los resultados por páginas con `window.__occ_page(0)`, `(1)`... (≤600 caracteres).
// Con esas filas se arma el JSON para `gmaj add-jobs` (description = sueldo + extracto). No uses un servidor local: Chrome pide
// permiso de red local y congela la pestaña. ("Ya estás postulado" aparece en todas las tarjetas; no sirve de señal. La DB deduplica por URL.)
window.__occ_done = null;
(async () => {
  const QUERIES = __QUERIES__;
  const MODES = [['tipo-home-office-remoto', 'remote'], ['tipo-hibrido', 'hybrid']];
  const MAX_PER_SEARCH = 5;
  const parse = (html) => new DOMParser().parseFromString(html, 'text/html');
  const flat = (node) => node.textContent.replace(/\s+/g, ' ').trim();
  const found = new Map();
  for (const q of QUERIES) for (const [seg, mode] of MODES) {
    try {
      const r = await fetch(`/empleos/de-${q}/${seg}/`, {credentials: 'include'});
      if (!r.ok) continue;
      for (const c of [...parse(await r.text()).querySelectorAll('li.vacancy-card[data-id], .card-job-offer[data-id]')].slice(0, MAX_PER_SEARCH)) {
        if (!found.has(c.dataset.id)) found.set(c.dataset.id, mode);
      }
    } catch (e) {}
    await new Promise(r => setTimeout(r, 300));
  }
  const jobs = [];
  for (const [id, searchMode] of found) {
    try {
      const url = `https://www.occ.com.mx/empleo/oferta/${id}/`;
      const doc = parse(await (await fetch(url, {credentials: 'include'})).text());
      const text = flat(doc.body);
      const title = doc.title.replace(/^Trabajo de /, '').replace(/ - \d+ \| OCC$/, '').trim();
      // La página trae vacantes recomendadas antes de la oferta: acotar al bloque que va entre "Compartir en X" y "Sobre el empleo".
      const end = text.indexOf('Sobre el empleo');
      const seg = text.slice(Math.max(0, text.lastIndexOf('Compartir en X', end)), end);
      const co = seg.match(/(?:Mensual|conocer el sueldo|Sueldo no mostrado por la empresa)\s+(.+?) en (.+?)(?: Empresa verificada| Postularme| Sé de los primeros|$)/);
      const espacio = (text.match(/Espacio de trabajo:\s*(Desde casa|Presencial|H[ií]brido|Remoto|\S+)/) || [])[1] || '';
      const mode = /remot|casa/i.test(espacio) ? 'remote' : /h[ií]brid/i.test(espacio) ? 'hybrid' : /presencial/i.test(espacio) ? 'onsite' : searchMode;
      const sal = (seg.match(/\$\s?[\d,]+(?:\s*-\s*\$\s?[\d,]+)?\s*Mensual/) || [])[0] || '';
      const desc = text.split(' Descripción ')[1] || text;
      jobs.push({source: 'occ', external_id: id, url, title, company: co ? co[1] : '', location: co ? co[2] : '', mode,
                 description: (sal ? 'Sueldo: ' + sal + '. ' : '') + `Espacio de trabajo: ${espacio || searchMode}. ` + desc.slice(0, 900)});
    } catch (e) {}
    await new Promise(r => setTimeout(r, 300));
  }
  const floor = (j) => { const m = (j.description.match(/Sueldo: \$\s?([\d,]+)/) || [])[1]; return m ? parseInt(m.replace(/,/g, '')) : null; };
  const keep = jobs.filter(j => (__KEEP_ONSITE__ || j.mode !== 'onsite') && j.title && !(floor(j) !== null && floor(j) < __FLOOR__));
  const legal = new RegExp(__RELEVANT__, 'i');
  window.__occ = keep.filter(j => legal.test(j.title));
  const rows = window.__occ.map(j => [j.external_id, j.mode, j.title, j.company, j.location,
    (j.description.match(/Sueldo: [^.]*/) || ['s/d'])[0].replace('Sueldo: ', ''), j.description.replace(/^.*?Espacio de trabajo: \S+( casa)?\. /, '').slice(0, 90)]);
  const pages = []; let cur = [];
  for (const row of rows) { if (JSON.stringify([...cur, row]).length > 600 && cur.length) { pages.push(cur); cur = []; } cur.push(row); }
  if (cur.length) pages.push(cur);
  window.__occ_page = (n) => JSON.stringify(pages[n] || null);
  window.__occ_done = {collected: keep.length, legal: rows.length, pages: pages.length};
})(); 'started'
