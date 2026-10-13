"""Deterministic hard filters from user/search.yaml; never imply candidate work authorization."""
import re

from . import db


def phrase(text, term):
    return bool(re.search(r'(?<!\w)' + re.escape(db.normalize(term)).replace(r'\ ', r'\s+') + r'(?!\w)', db.normalize(text)))


def base_currency(config):
    return (config.get('currency') or {}).get('base', 'MXN').upper()


def monthly_amount(job, config):
    """Posted minimum salary converted to the user's base currency per month (None if unknown/unconvertible)."""
    amount = job.get('salary_min')
    if amount is None:
        return None
    base = base_currency(config)
    currency = (job.get('salary_currency') or '').upper()
    rates = {k.upper(): v for k, v in ((config.get('currency') or {}).get('rates') or {}).items()}
    factor = 1 if currency == base else rates.get(currency)
    period = {'hour': 173, 'month': 1, 'year': 1 / 12}.get(job.get('salary_period'))
    return float(amount) * factor * period if factor is not None and period is not None else None


FOREIGN_MARKERS = {
    # Matched after accent stripping, so avoid words shared with Spanish (beneficios, regulatorio...).
    'pt': ['você', 'vagas', 'qualificações', 'conhecimento', 'atuação', 'desejável', 'estágio', 'não'],
    'de': ['wir suchen', 'deine aufgaben', 'ihre aufgaben', 'kenntnisse', 'bewerbung', 'm w d', 'werkstudent'],
    'fr': ['vous', 'nous recherchons', 'compétences', 'expérience requise'],
}


def foreign_language(job, config):
    allowed = config.get('languages_allowed', ['en', 'es'])
    text = db.normalize(' '.join(str(job.get(k) or '') for k in ('title', 'description')))
    for lang, markers in FOREIGN_MARKERS.items():
        if lang not in allowed and sum(phrase(text, m) for m in markers) >= 2:
            return lang
    return None


HYBRID_MARKERS = ['hybrid', 'híbrido', 'hibrido', 'esquema mixto', 'days in office', 'days a week in the office',
                  'días en oficina', 'dias en oficina', 'días presenciales', 'dias presenciales']
ONSITE_MARKERS = ['on-site', 'onsite', 'in-office', 'in office full time', 'presencial', '100% en oficina',
                  'trabajo en sitio', 'en sitio']


def actual_work_mode(job):
    """Job boards' remote flags are unreliable (LinkedIn lists hybrid/on-site roles as remote); trust the text."""
    text = db.normalize(' '.join(str(job.get(k) or '') for k in ('title', 'description')))
    if any(phrase(text, m) for m in HYBRID_MARKERS):
        return 'hybrid'
    if any(phrase(text, m) for m in ONSITE_MARKERS) and not phrase(text, 'remote') and not phrase(text, 'remoto'):
        return 'onsite'
    return job.get('work_mode', 'unknown')


def office_rule(job, mode, salary, config):
    """Hybrid/on-site policy: accept | reject | zones (commute zones ok / ask / reject). None = passes."""
    wm = config.get('work_mode', {})
    policy = wm.get(mode, 'reject')
    cur = base_currency(config)
    if policy == 'reject':
        return 'discarded', f'{mode} work not accepted'
    office_min = (config.get('salary') or {}).get('office_min_month')
    if office_min and salary is not None and salary < office_min:
        return 'discarded', f'{mode} salary {salary:.2f} {cur}/month below office minimum'
    if policy == 'accept':
        return None
    zones = wm.get('zones') or {}
    where = ' '.join(str(job.get(k) or '') for k in ('location', 'description'))
    if any(phrase(where, z) for z in zones.get('reject', [])):
        return 'discarded', f'{mode} in a rejected commute zone'
    if any(phrase(where, z) for z in zones.get('ask', [])):
        return 'needs_user', f'{mode} in a far commute zone; ask the candidate'
    if any(phrase(job.get('location') or '', z) for z in zones.get('ok', [])):
        return 'filtered', f'{mode} in an accepted zone; use the office salary expectation'
    return 'discarded', f'{mode} outside accepted zones'


def evaluate(job, config):
    job = {**job, 'work_mode': actual_work_mode(job)}
    lang = foreign_language(job, config)
    if lang:
        return 'discarded', f'Language not allowed: {lang}'
    exclusions = config.get('exclusions') or {}
    for company in exclusions.get('companies', []):
        if db.normalize(company) == db.normalize(job.get('company')):
            return 'discarded', f'Excluded company: {company}'
    for term in exclusions.get('off_target_title_keywords', []):
        if phrase(job.get('title', ''), term):
            return 'discarded', f'Off-target title: {term}'
    for term in exclusions.get('title_keywords', []):
        if phrase(job.get('title', ''), term):
            return 'discarded', f'Excluded title: {term}'
    mode = job.get('work_mode', 'unknown')
    eligibility = config.get('eligibility') or {}
    text = ' '.join(str(job.get(k) or '') for k in ('title', 'location', 'description'))
    accepts = [p for p in eligibility.get('accept_phrases', []) if phrase(text, p)]
    # Contractor is a contract type, not evidence of geographic eligibility.
    accepts = [p for p in accepts if db.normalize(p) != 'contractor']
    for term in eligibility.get('reject_phrases', []):
        if not phrase(text, term):
            continue
        if db.normalize(term) == 'no visa sponsorship' and not any(phrase(text, p) for p in ('united states', 'usa', 'us only', 'u.s.', 'us residents')):
            continue
        if not accepts:
            return 'discarded', f'Eligibility restriction: {term}'
    # Remote roles pinned to another country (e.g. LinkedIn "Remote" in Bogotá/São Paulo/US) usually require residence there.
    location = job.get('location') or ''
    allowed = eligibility.get('location_ok', [])
    if allowed and location.strip() and not any(phrase(location, p) for p in allowed) and not accepts:
        return 'discarded', f'Location outside allowed regions: {location[:60]}'
    salary = monthly_amount(job, config)
    cur = base_currency(config)
    floor = (config.get('salary') or {}).get('floor_month')
    if floor and salary is not None and salary < floor:
        return 'discarded', f'Salary {salary:.2f} {cur}/month below floor'
    if mode in ('hybrid', 'onsite'):
        decision = office_rule(job, mode, salary, config)
        if decision:
            return decision
    return 'filtered', 'Passed hard filters' + ('; salary unknown/unconvertible' if salary is None else f'; {salary:.2f} {cur}/month')


def run(conn, config):
    counts = {}
    for row in conn.execute("SELECT * FROM jobs WHERE status='new'").fetchall():
        status, reason = evaluate(dict(row), config)
        db.set_status(conn, row['id'], status, note=reason, filter_reason=reason)
        counts[status] = counts.get(status, 0) + 1
    return counts
