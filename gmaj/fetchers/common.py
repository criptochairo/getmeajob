import logging
import random
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from .. import db, paths
from ..cv_language import detect_text_language

LOG = logging.getLogger('fetch')

def clean(value):
    text = BeautifulSoup(str(value or ''), 'html.parser').get_text(' ', strip=True)
    # Greenhouse can return entity-escaped HTML rather than literal tags.
    if re.search(r'</?[a-zA-Z][^>]*>', text):
        text = BeautifulSoup(text, 'html.parser').get_text(' ', strip=True)
    return text

def queries(config):
    return list(dict.fromkeys(q for values in config['queries'].values() for q in values))

def relevance_keywords(config):
    """search.yaml relevance_keywords: words that make a title worth storing (built from the user's role families)."""
    return [db.normalize(k) for k in config.get('relevance_keywords', []) if str(k).strip()]

def relevant(title, config, description=''):
    text = db.normalize(title + ' ' + description)
    return (any(re.search(r'\b' + re.escape(k) + r'(?:s|es)?\b', text) for k in relevance_keywords(config))
            or any(db.normalize(q) in text for q in queries(config)))

def work_mode(text='', remote=False, explicit=None):
    text = db.normalize(str(explicit or '') + ' ' + str(text))
    if re.search(r'\b(hybrid|hibrido|hibrida)\b', text):
        return 'hybrid'
    if re.search(r'\b(onsite|on site|presencial|office based)\b', text):
        return 'onsite'
    if remote or re.search(r'\b(remote|remoto|remota|teletrabajo|home office)\b', text):
        return 'remote'
    return 'unknown'

def salary(text='', low=None, high=None, currency=None, period=None):
    text = clean(text)
    structured_amount = low is not None
    # Parse only an amount explicitly accompanied by a currency marker.
    match = re.search(r'(USD|MXN|US\$|MX\$|\$|€|EUR|GBP|£)\s*(\d[\d,.]*\s*[kK]?)\s*(?:[-–—]|to|a)?\s*(?:(?:USD|MXN|US\$|MX\$|\$|€|EUR|GBP|£)\s*)?(\d[\d,.]*\s*[kK]?)?', text, re.I)
    def number(v):
        if v is None or v == '':
            return None
        try:
            s = str(v).strip().lower().replace(',', '')
            return float(s.rstrip('k').strip()) * (1000 if s.endswith('k') else 1)
        except ValueError:
            return None
    if match and low is None:
        low, high = number(match[2]), number(match[3])
    currency = str(currency or '').upper() or None
    if currency is None and match and not structured_amount:
        currency = {'US$': 'USD', 'MX$': 'MXN', '€': 'EUR', '£': 'GBP'}.get(match[1].upper(), match[1].upper())
        if currency == '$':
            currency = None  # A bare dollar sign does not establish USD versus MXN.
    # A payment interval elsewhere in a long description can concern expenses
    # or a different role. Prefer the API interval, otherwise use nearby text.
    nearby = text[max(0, match.start() - 20):match.end() + 60] if match else text[:100]
    period_text = db.normalize(str(period) if period else nearby)
    normalized = 'unknown'
    for value, terms in [('hour', ('hour', 'hourly', 'hr', 'h', 'hora', 'por hora')), ('month', ('month', 'monthly', 'mensual', 'mes')), ('year', ('year', 'yearly', 'annual', 'annually', 'anual', 'ano'))]:
        if any(re.search(r'\b' + t + r'\b', period_text) for t in terms):
            normalized = value
            break
    return dict(salary_min=number(low), salary_max=number(high), salary_currency=currency, salary_period=normalized)

def posted(value):
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc).isoformat()
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).isoformat()
    except (ValueError, OverflowError, OSError):
        try:
            return parsedate_to_datetime(str(value)).isoformat()
        except (ValueError, TypeError):
            return str(value)

def job(source, title, company, url, external_id=None, location='', description='', remote=False, mode=None, date=None, language=None, **pay):
    description = clean(description)
    location = clean(location)
    record = dict(source=source, external_id=str(external_id) if external_id is not None else None,
                url=url, title=clean(title), company=clean(company), location=location,
                work_mode=work_mode(location + ' ' + clean(title), remote, mode), description=description,
                language=language or detect_text_language(clean(title) + ' ' + description) or 'en',
                posted_at=posted(date), fetched_at=db.now(), updated_at=db.now(), status='new',
                **salary(**pay))
    record['id'] = db.job_id(record) if url else None
    return {field: record.get(field) for field in db.FIELDS}

class Client:
    def __init__(self, source, options=None):
        self.source = source
        self.options = options if isinstance(options, dict) else {}
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        self.last_request = 0
        self.errors = []
        self.slowdown = 0.0   # freno adaptativo: segundos extra entre peticiones tras un 429 (ver throttle)

    def error(self, context, error):
        message = f'{self.source}: {context}: {error}'
        self.errors.append(message)
        LOG.warning(message)

    def throttle(self, hit_429):
        """Freno adaptativo, solo si la fuente define adaptive_step_seconds: cada 429 duplica el retraso extra
        (hasta adaptive_max_seconds) y cada éxito lo reduce ×adaptive_decay. Un ritmo fijo vuelve a chocar con
        el límite una y otra vez; LinkedIn guest, por ejemplo, tolera ~1 petición/min sostenida."""
        step = float(self.options.get('adaptive_step_seconds', 0))
        if not step:
            return
        if hit_429:
            self.slowdown = min(float(self.options.get('adaptive_max_seconds', 120)), max(step, self.slowdown * 2))
            LOG.info('%s: freno adaptativo +%.0f s entre peticiones', self.source, self.slowdown)
        else:
            self.slowdown *= float(self.options.get('adaptive_decay', 0.9))

    def get(self, url, **kwargs):
        # 429: espera progresiva (Retry-After si viene; si no, backoff_429 s × intento) antes de rendirse.
        attempts = 1 + int(self.options.get('retries_429', 1))
        for attempt in range(attempts):
            delay = float(self.options.get('delay_seconds', 0.4)) + random.uniform(0, float(self.options.get('delay_jitter', 0))) + self.slowdown
            time.sleep(max(0, delay - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(url, timeout=(10, 25), **kwargs)
                if response.status_code == 429:
                    self.throttle(True)
                elif response.status_code < 400:
                    self.throttle(False)
                if response.status_code == 404:
                    response.raise_for_status()
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                response = getattr(exc, 'response', None)
                if attempt == attempts - 1 or (response is not None and response.status_code not in (429,) and response.status_code < 500):
                    raise
                if response is not None and response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '')
                    wait = float(retry_after) if retry_after.isdigit() else float(self.options.get('backoff_429', 1)) * (attempt + 1)
                    LOG.info('%s: 429, esperando %.0f s (intento %d/%d)', self.source, wait, attempt + 1, attempts)
                    time.sleep(wait)
                else:
                    time.sleep(1)

    def live_slugs(self, slugs):
        """Salta las bolsas que ya dieron 404 (user/data/invalid_boards.txt); borra la línea para reintentar una."""
        path = paths.data('invalid_boards.txt')
        dead = set(path.read_text(encoding='utf-8').splitlines()) if path.exists() else set()
        for slug in slugs:
            if f'{self.source}/{slug}' in dead:
                LOG.info('%s: salto %s (404 antes; ver invalid_boards.txt)', self.source, slug)
                continue
            yield slug

    def invalid_board(self, slug):
        path = paths.data('invalid_boards.txt')
        path.parent.mkdir(parents=True, exist_ok=True)
        line = f'{self.source}/{slug}'
        previous = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
        if line not in previous:
            with path.open('a', encoding='utf-8') as stream:
                stream.write(line + '\n')

    def board_error(self, slug, exc):
        if getattr(exc, 'response', None) is not None and exc.response.status_code == 404:
            self.invalid_board(slug)
        self.error(slug, exc)
