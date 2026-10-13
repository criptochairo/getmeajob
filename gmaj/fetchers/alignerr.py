"""Alignerr (Labelbox): trabajos remotos por hora de entrenamiento de IA.

API pública JSON de www.alignerr.com/jobs (sin sesión): /api/jobs?search=<t>&offset=<n>&limit=<n> → {jobs, total, offset, limit};
cada job: id, title, description, pay ("$20-40/hr"), location, applyUrl, category. Se aplica en app.alignerr.com con la sesión del usuario.
Publican la misma vacante por ciudad/idioma: se deduplica por título normalizado y se prefiere la de ubicación "Remote"/región del usuario.
"""
import re
from .common import job, relevant

def fetch(config, client):
    best = {}
    limit = int(client.options.get('page_size', 100))
    local_words = client.options.get('local_words') or ['remote', 'latam', 'latin']
    local_re = re.compile('|'.join(re.escape(w) for w in local_words), re.I)
    for term in client.options.get('search_terms') or config.get('relevance_keywords', [])[:8]:
        offset = 0
        while True:
            data = client.get(client.options['url'], params={'search': term, 'offset': offset, 'limit': limit}).json()
            items = data.get('jobs', [])
            for item in items:
                # "(Remote Contract)" va en casi todos los títulos: quitarlo para que "contract" no cuente como señal de relevancia.
                title = re.sub(r'\b(remote )?contract\b(?! (manager|specialist|analyst|review|drafting|law))', '', item['title'], flags=re.I)
                if not relevant(title, config):
                    continue
                key = re.sub(r'\W+', ' ', item['title'].lower()).strip()
                local = local_re.search(item.get('location') or '')
                if key not in best or (local and not best[key][1]):
                    best[key] = (item, bool(local))
            offset += len(items)
            if not items or offset >= int(data.get('total', 0)):
                break
    for item, _ in best.values():
        pay = item.get('pay') or ''
        low_high = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', pay)[:2]]
        yield job('alignerr', item['title'], 'Alignerr', 'https://app.alignerr.com/signin?job=' + item['id'], item['id'],
                  item.get('location') or 'Remote', f"Pago: {pay}. Categoría: {item.get('category', '')}. {item.get('description', '')}",
                  remote=True, low=low_high[0] if low_high else None, high=low_high[-1] if low_high else None,
                  currency='USD' if '$' in pay else None, period='hour' if '/hr' in pay else None)
