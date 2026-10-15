"""SQLite storage and atomic state history for the discovery pipeline."""
import hashlib
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import paths

ROOT = paths.ROOT
AGENTS = ('claude', 'codex', 'human')
STATES = ('new', 'filtered', 'discarded', 'scored', 'tailored', 'reviewed',
          'approved', 'applied', 'needs_user', 'rejected', 'failed')
FIELDS = ('id source external_id url title company location work_mode salary_min '
          'salary_max salary_currency salary_period description language posted_at '
          'fetched_at status filter_reason score score_reason app_dir assigned_agent updated_at').split()

def now():
    return datetime.now(timezone.utc).isoformat()

def normalize(value):
    value = unicodedata.normalize('NFKD', str(value or '').casefold())
    return ' '.join(re.sub(r'[^\w]+', ' ', ''.join(c for c in value if not unicodedata.combining(c))).split())

def normalize_url(url):
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith('utm_') and k.lower() not in ('ref', 'source', 'trk')]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), urlencode(sorted(query)), ''))

# Reposts of one vacancy often differ only by a location/modality suffix ("Paralegal - Remote, Mexico").
PLACE_WORDS = re.compile(r'\b(remote|remoto|remota|hybrid|hibrido|hibrida|on ?site|presencial|home office|latam|'
                         r'latin america|mexico|cdmx|usa|us only|uk|emea|americas|worldwide|anywhere)\b')


def title_key(title):
    raw = unicodedata.normalize('NFKD', str(title or '').casefold())
    raw = ''.join(c for c in raw if not unicodedata.combining(c))
    raw = re.sub(r'[(\[][^)\]]*[)\]]', lambda m: '' if PLACE_WORDS.search(m.group()) else m.group(), raw)
    parts = re.split(r'\s+[-–—|·]\s+|,\s*', raw)
    while len(parts) > 1 and PLACE_WORDS.search(parts[-1]):
        parts.pop()
    return normalize(' '.join(parts)) or normalize(title)


def job_id(job):
    key = f"{job['source']}:{job['external_id']}" if job.get('external_id') else normalize_url(job['url'])
    return hashlib.sha1(key.encode()).hexdigest()

def connect(path=None):
    path = Path(path or paths.data('jobs.db'))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    states = ','.join(repr(s) for s in STATES)
    conn.executescript(f"""
    CREATE TABLE IF NOT EXISTS jobs (
      id TEXT PRIMARY KEY, source TEXT, external_id TEXT, url TEXT NOT NULL,
      title TEXT NOT NULL, company TEXT, location TEXT,
      work_mode TEXT CHECK(work_mode IN ('remote','hybrid','onsite','unknown')),
      salary_min REAL, salary_max REAL, salary_currency TEXT,
      salary_period TEXT CHECK(salary_period IN ('hour','month','year','unknown')),
      description TEXT, language TEXT,
      posted_at TEXT, fetched_at TEXT, status TEXT NOT NULL CHECK(status IN ({states})),
      filter_reason TEXT, score INTEGER, score_reason TEXT, app_dir TEXT,
      assigned_agent TEXT, updated_at TEXT, company_key TEXT, title_key TEXT);
    CREATE TABLE IF NOT EXISTS events (
      job_id TEXT NOT NULL REFERENCES jobs(id), ts TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ({states})), note TEXT);
    DROP INDEX IF EXISTS jobs_company_title;
    CREATE INDEX IF NOT EXISTS jobs_company_title_key ON jobs(company_key,title_key);
    CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);
    CREATE INDEX IF NOT EXISTS jobs_url ON jobs(url);
    """)
    return conn

def insert_job(conn, job):
    """Refresh discovery metadata for the same new ID; never reset agent state."""
    job = dict(job)
    job['id'] = job_id(job)
    job['url'] = normalize_url(job['url'])
    existing = conn.execute('SELECT id,status FROM jobs WHERE id=? OR url=?', (job['id'], job['url'])).fetchone()
    if existing:
        if existing['id'] == job['id'] and existing['status'] == 'new':
            refresh = {k: job[k] for k in ('location', 'work_mode', 'salary_min', 'salary_max',
                       'salary_currency', 'salary_period', 'description', 'language', 'posted_at') if k in job}
            refresh.update(fetched_at=now(), updated_at=now())
            with conn:
                conn.execute('UPDATE jobs SET ' + ','.join(f'{k}=?' for k in refresh) + " WHERE id=? AND status='new'", [*refresh.values(), existing['id']])
        return False
    job.update(status='new', fetched_at=now(), updated_at=now())
    job.setdefault('work_mode', 'unknown')
    job.setdefault('salary_period', 'unknown')
    job.setdefault('language', 'en')
    columns = FIELDS + ['company_key', 'title_key']
    company, title = normalize(job.get('company')), title_key(job.get('title'))
    if company and title and is_repost(conn, company, title, job.get('location')):
        return False
    values = [job.get(k) for k in FIELDS] + [company, title]
    with conn:
        cur = conn.execute(f"INSERT OR IGNORE INTO jobs ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
        if not cur.rowcount:
            return False
        conn.execute('INSERT INTO events VALUES (?,?,?,?)', (job['id'], now(), 'new', 'Fetched from ' + job['source']))
    return True

def is_repost(conn, company, title, location):
    """Same company and title already stored in the same place, or one that already passed the filters.
    Copies elsewhere that are still unfiltered (or discarded) are kept: a US-only "Data Analyst" must not hide
    the Mexico one. prefilter.run removes the duplicates that survive the filters."""
    rows = conn.execute('SELECT status,location FROM jobs WHERE company_key=? AND title_key=?', (company, title)).fetchall()
    return any(r['status'] not in ('new', 'discarded') or normalize(r['location']) == normalize(location) for r in rows)


def set_status(conn, ident, status, note=None, app_dir=None, agent=None, **extra):
    if status not in STATES:
        raise ValueError(f'Invalid status: {status}')
    if agent is not None and agent not in AGENTS:
        raise ValueError('Invalid agent')
    if set(extra) - {'filter_reason', 'score', 'score_reason', 'work_mode'}:
        raise ValueError('Invalid update fields')
    updates = {'status': status, 'updated_at': now(), **extra}
    if app_dir is not None:
        updates['app_dir'] = app_dir
    if agent is not None:
        updates['assigned_agent'] = agent
    with conn:
        old = conn.execute('SELECT status FROM jobs WHERE id=?', (ident,)).fetchone()
        if not old:
            raise ValueError(f'Unknown job: {ident}')
        conn.execute('UPDATE jobs SET ' + ','.join(f'{k}=?' for k in updates) + ' WHERE id=?', [*updates.values(), ident])
        if old['status'] != status:
            conn.execute('INSERT INTO events VALUES (?,?,?,?)', (ident, now(), status, note))
        if status == 'discarded' and old['status'] not in ('new', 'discarded'):
            # The copy that won the dedupe fell later (e.g. hybrid once checked in the browser): give its twins
            # another chance; prefilter.run re-evaluates them as new.
            conn.execute("UPDATE jobs SET status='new', updated_at=? WHERE status='discarded' AND filter_reason LIKE ?",
                         (now(), f'Duplicate of {ident[:8]}%'))
