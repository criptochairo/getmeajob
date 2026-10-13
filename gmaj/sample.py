"""Market signal for role suggestions: how many postings each query has in the user's market.

Counts search-result cards only (no detail requests). Numbers are lower bounds, only meant to compare candidate
roles with each other. LinkedIn is treated with care: same pauses as the daily fetch, one page per query, at most
MAX_LINKEDIN_QUERIES per run, and it is skipped while the shared cool-down is active (gmaj/cooldown.py).
"""
import re

from bs4 import BeautifulSoup

from . import config, cooldown, db
from .fetchers.common import Client
from .fetchers.linkedin_guest import SOURCE as LINKEDIN, blocked

WEEK = 'r604800'
MAX_LINKEDIN_QUERIES = 8


def linkedin(client, query, location):
    html = client.get('https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search',
                      params={'keywords': query, 'location': location, 'start': 0, 'f_TPR': WEEK}).text
    cards = BeautifulSoup(html, 'html.parser').select('div.base-search-card, div.base-card')
    return f'{len(cards)}+' if len(cards) >= 10 else str(len(cards))


def computrabajo(client, query, base):
    slug = re.sub(r'[^a-z0-9]+', '-', db.normalize(query)).strip('-')
    html = client.get(f'{base}/trabajo-de-{slug}').text
    cards = BeautifulSoup(html, 'html.parser').select('article.box_offer, div.box_offer')
    return f'{len(cards)}+' if len(cards) >= 20 else str(len(cards))


def himalayas(client, query):
    data = client.get('https://himalayas.app/jobs/api/search', params={'q': query, 'page': 1}).json()
    return str(data.get('totalCount', len(data.get('jobs', []))))


def run(queries, location=None, computrabajo_base=None, li_client=None, other_client=None):
    try:
        cfg = config.search()
    except config.MissingUserFile:
        cfg = {}
    location = location or config.get(cfg, 'market.linkedin_location') or config.get(cfg, 'market.country_label') or 'Mexico'
    computrabajo_base = computrabajo_base or config.get(cfg, 'sources.computrabajo.url')
    # Same pacing as the daily fetch; no retries: on the first block we stop and start the shared cool-down.
    li = li_client or Client(LINKEDIN, {'delay_seconds': 5, 'delay_jitter': 4, 'retries_429': 0})
    other = other_client or Client('sample', {'delay_seconds': 1})
    paused = cooldown.active(LINKEDIN)
    li_status = cooldown.describe(paused) if paused else None
    li_used = 0
    results = []
    for query in queries:
        row = {'query': query}
        if li_status:
            row['linkedin'] = li_status
        elif li_used >= MAX_LINKEDIN_QUERIES:
            row['linkedin'] = f'omitido (máximo {MAX_LINKEDIN_QUERIES} consultas a LinkedIn por corrida)'
        else:
            li_used += 1
            try:
                row['linkedin'] = linkedin(li, query, location)
            except Exception as exc:
                if blocked(exc):
                    li_status = cooldown.describe(cooldown.start(LINKEDIN, 'bloqueo durante el conteo de mercado'))
                    row['linkedin'] = li_status
                else:
                    row['linkedin'] = f'error: {str(exc)[:60]}'
        for name, call in (('computrabajo', lambda: computrabajo(other, query, computrabajo_base) if computrabajo_base else None),
                           ('himalayas_remote', lambda: himalayas(other, query))):
            try:
                value = call()
                if value is not None:
                    row[name] = value
            except Exception as exc:
                row[name] = f'error: {str(exc)[:60]}'
        results.append(row)
    return {'location': location,
            'notes': {'linkedin': 'primera página de los últimos 7 días ("10+" = página llena); máx. 8 consultas por corrida',
                      'computrabajo': 'primera página de resultados, sin filtro de fecha ("20+" = página llena)',
                      'himalayas_remote': 'total de vacantes remotas globales que coinciden, sin filtro de fecha'},
            'results': results}
