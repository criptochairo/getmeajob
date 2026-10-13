import re
import time
from datetime import datetime, timezone
from urllib.parse import parse_qsl
from bs4 import BeautifulSoup
from .common import job, queries, relevant, LOG

def parse_cards(html):
    soup = BeautifulSoup(html, 'html.parser')
    for card in soup.select('div.base-search-card, div.base-card'):
        title = card.select_one('.base-search-card__title')
        company = card.select_one('.base-search-card__subtitle')
        location = card.select_one('.job-search-card__location')
        link = card.select_one('a.base-card__full-link')
        if title is None or link is None:
            continue
        url = link.get('href', '').split('?')[0]
        ident = re.search(r'(?:jobPosting:|[-/])(\d+)(?:$|[/?])', card.get('data-entity-urn', '') or url)
        if ident:
            yield dict(title=title.get_text(strip=True), company=company.get_text(strip=True) if company else '',
                       location=location.get_text(strip=True) if location else '', url=url, external_id=ident[1])

def passes(options):
    """Search passes: each has locations, a LinkedIn work-type filter and an optional forced mode (hybrid)."""
    if options.get('passes'):
        return options['passes']
    return [{'locations': options.get('locations', ['Mexico']), 'filter': options.get('remote_filter', '')}]

def window_seconds(client):
    """f_TPR: publicadas en las últimas `posted_within_hours` (48 h); si la última corrida fue hace más, cubrir el hueco (+24 h). Tope 7 días."""
    base = int(client.options.get('posted_within_hours', 48)) * 3600
    last = getattr(client, 'last_fetched', None)
    if last:
        try:
            gap = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() + 86400
            base = max(base, int(gap))
        except ValueError:
            pass
    return min(base, 7 * 86400)

def query_groups(config, size):
    """Agrupa las consultas con OR para hacer menos búsquedas (LinkedIn acepta booleanos en keywords)."""
    items = queries(config)
    if size <= 1:
        return items
    return [' OR '.join(f'"{q}"' for q in items[i:i + size]) for i in range(0, len(items), size)]

def blocked(exc):
    return getattr(exc, 'response', None) is not None and exc.response.status_code in (403, 429)

def fetch(config, client):
    seen = set()
    tpr = f'r{window_seconds(client)}'
    LOG.info('linkedin_guest: f_TPR=%s', tpr)
    max_pages = int(client.options.get('max_pages_per_query', 2))
    pause = float(client.options.get('pause_on_block_seconds', 300))
    max_blocks = int(client.options.get('max_consecutive_blocks', 3))
    strikes = 0
    for query in query_groups(config, int(client.options.get('or_group_size', 5))):
        LOG.info('linkedin_guest: query %s', query)
        for spec in passes(client.options):
          for location in spec['locations']:
            for page in range(max_pages):
                params = {'keywords': query, 'location': location, 'start': page * 10, 'f_TPR': tpr,
                          **dict(parse_qsl(spec.get('filter', '')))}
                try:
                    html = client.get(client.options['url'], params=params).text
                    strikes = 0
                except Exception as exc:
                    client.error(f'{query}/{location}/page {page}', exc)
                    if blocked(exc):
                        strikes += 1
                        if strikes >= max_blocks:
                            client.error('remaining queries', f'Skipped after {strikes} consecutive blocks')
                            return
                        LOG.info('linkedin_guest: bloqueado (%d/%d), pausa %.0f s y sigo con la siguiente búsqueda', strikes, max_blocks, pause)
                        time.sleep(pause)
                    break
                cards = list(parse_cards(html))
                if not cards:
                    if BeautifulSoup(html, 'html.parser').get_text(strip=True):
                        client.error(f'{query}/{location}', 'No recognizable job cards (empty results or changed/blocked HTML)')
                    break
                fresh = 0
                for card in cards:
                    if card['external_id'] in seen or card['external_id'] in getattr(client, 'known', ()):
                        continue
                    fresh += 1
                    seen.add(card['external_id'])
                    if not relevant(card['title'], config):
                        continue
                    try:
                        detail = BeautifulSoup(client.get('https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/' + card['external_id']).text, 'html.parser')
                    except Exception as exc:
                        client.error(card['external_id'], exc)
                        if blocked(exc):
                            break   # la búsqueda siguiente la decide el contador de bloqueos
                        continue
                    desc = detail.select_one('.show-more-less-html__markup')
                    if desc is None:
                        client.error(card['external_id'], 'Description missing; skipping incomplete posting')
                        continue
                    date = detail.select_one('time')
                    mode = 'hybrid' if re.search(r'hybrid', desc.get_text().lower()) else None
                    yield job('linkedin_guest', **card, description=str(desc), remote=True, mode=mode,
                              date=date.get('datetime') if date else None, text=str(desc))
                # Página siguiente solo si esta vino llena y todo era nuevo (si no, ya alcanzamos lo conocido).
                if len(cards) < 10 or fresh < len(cards):
                    break
