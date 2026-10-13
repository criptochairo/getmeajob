"""Market signal for role suggestions: how many postings each query has in the user's market in the last 7 days.

Counts search-result cards only (no detail requests), so it is fast and polite. Numbers are lower bounds
("30+" means at least three full pages) and only meant to compare candidate roles with each other.
"""
import re

from bs4 import BeautifulSoup

from . import config, db
from .fetchers.common import Client

WEEK = 'r604800'


def linkedin(client, query, location, pages=3):
    total = 0
    for page in range(pages):
        html = client.get('https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search',
                          params={'keywords': query, 'location': location, 'start': page * 10, 'f_TPR': WEEK}).text
        cards = BeautifulSoup(html, 'html.parser').select('div.base-search-card, div.base-card')
        total += len(cards)
        if len(cards) < 10:
            return str(total)
    return f'{total}+'


def computrabajo(client, query, base):
    slug = re.sub(r'[^a-z0-9]+', '-', db.normalize(query)).strip('-')
    html = client.get(f'{base}/trabajo-de-{slug}').text
    cards = BeautifulSoup(html, 'html.parser').select('article.box_offer, div.box_offer')
    return f'{len(cards)}+' if len(cards) >= 20 else str(len(cards))


def himalayas(client, query):
    data = client.get('https://himalayas.app/jobs/api/search', params={'q': query, 'page': 1}).json()
    return str(data.get('totalCount', len(data.get('jobs', []))))


def run(queries, location=None, computrabajo_base=None):
    try:
        cfg = config.search()
    except config.MissingUserFile:
        cfg = {}
    location = location or config.get(cfg, 'market.linkedin_location') or config.get(cfg, 'market.country_label') or 'Mexico'
    computrabajo_base = computrabajo_base or config.get(cfg, 'sources.computrabajo.url')
    li = Client('linkedin_guest', {'delay_seconds': 3, 'delay_jitter': 2, 'retries_429': 1, 'backoff_429': 30})
    other = Client('sample', {'delay_seconds': 1})
    results = []
    for query in queries:
        row = {'query': query}
        for name, call in (('linkedin', lambda: linkedin(li, query, location)),
                           ('computrabajo', lambda: computrabajo(other, query, computrabajo_base) if computrabajo_base else None),
                           ('himalayas_remote', lambda: himalayas(other, query))):
            try:
                value = call()
                if value is not None:
                    row[name] = value
            except Exception as exc:
                row[name] = f'error: {str(exc)[:60]}'
        results.append(row)
    return {'location': location, 'window': '7 días', 'results': results}
