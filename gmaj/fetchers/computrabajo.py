import json
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .common import job, queries, relevant, db, work_mode

def parse_cards(html, base):
    soup = BeautifulSoup(html, 'html.parser')
    for card in soup.select('article.box_offer, div.box_offer'):
        link = card.select_one('h2 a[href], a.js-o-link[href]')
        if link is None:
            continue
        company = card.select_one('a.fc_base.t_ellipsis, .company')
        location = card.select_one('p.fs16.fc_base:not(.dFlex) span.mr10, [offer-localization], .location')
        tags = card.select_one('div.fs13.mt15')
        tag_text = tags.get_text(' ', strip=True) if tags else ''
        mode = 'hybrid' if 'presencial y remoto' in tag_text.casefold() else work_mode(tag_text)
        yield dict(title=link.get_text(strip=True), company=company.get_text(strip=True) if company else '',
                   location=location.get_text(strip=True) if location else '', url=urljoin(base, link['href']),
                   external_id=card.get('data-id'), mode=mode)

def parse_detail(html):
    soup = BeautifulSoup(html, 'html.parser')
    def postings(value):
        if isinstance(value, list):
            for item in value:
                yield from postings(item)
        elif isinstance(value, dict):
            if value.get('@type') == 'JobPosting':
                yield value
            yield from postings(value.get('@graph', []))
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            items = list(postings(json.loads(script.string or script.get_text())))
            if items:
                return items[0]
        except (ValueError, TypeError):
            continue
    desc = soup.select_one('[div-link="oferta"], .job-description, #job-description')
    return {'description': str(desc)} if desc else None

def fetch(config, client):
    base = client.options['url']
    seen = set()
    for query in queries(config):
        slug = re.sub(r'[^a-z0-9]+', '-', db.normalize(query)).strip('-')
        try:
            suffix = '-en-remoto' if client.options.get('modality') == 'remoto' else ''
            html = client.get(f'{base}/trabajo-de-{slug}{suffix}').text
            cards = list(parse_cards(html, base))
            if not cards:
                client.error(query, 'No recognizable cards; empty results, markup change or anti-bot')
            for card in cards:
                if card['url'] in seen or not relevant(card['title'], config):
                    continue
                seen.add(card['url'])
                try:
                    detail = parse_detail(client.get(card['url']).text)
                    if not detail or not detail.get('description'):
                        client.error(card['url'], 'Description missing; skipping incomplete posting')
                        continue
                    desc = detail['description']
                    pay = detail.get('baseSalary') or {}
                    pay = pay if isinstance(pay, dict) else {}
                    value = pay.get('value') or {}
                    value = value if isinstance(value, dict) else {'value': value}
                    card['title'] = detail.get('title') or card['title']
                    card['company'] = (detail.get('hiringOrganization') or {}).get('name') or card['company']
                    if detail.get('jobLocationType') == 'TELECOMMUTE' and card['mode'] == 'unknown':
                        card['mode'] = 'remote'
                    yield job('computrabajo', **card, description=desc, language=client.options.get('language', 'es'), text=desc,
                              remote=client.options.get('modality') == 'remoto', date=detail.get('datePosted'),
                              low=value.get('minValue', value.get('value')) or None, high=value.get('maxValue') or None,
                              currency=pay.get('currency') or detail.get('salaryCurrency'), period=value.get('unitText'))
                except Exception as exc:
                    client.error(card['url'], exc)
        except Exception as exc:
            client.error(query, exc)
            if getattr(exc, 'response', None) is not None and exc.response.status_code in (403, 429):
                client.error('remaining queries', 'Skipped because source is blocking/rate limiting requests')
                return
