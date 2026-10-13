"""Application folders: user/applications/<date>_<company>_<role>/ with job.md, then cv.md, cover.md, answers.json, PDFs, logs."""
import datetime as dt
import re

from . import db, paths
from .cv_language import cv_language


def slug(text, n=30):
    return re.sub(r'[^a-z0-9]+', '-', db.normalize(text))[:n].strip('-') or 'x'


def create(conn, row):
    """Idempotent: a job that already has a folder keeps it (running `top` twice never duplicates)."""
    lang, lang_reason = cv_language(row['title'], row['description'])
    if row['app_dir'] and paths.user(row['app_dir']).exists():
        return {'id': row['id'], 'dir': row['app_dir'], 'title': row['title'], 'company': row['company'],
                'score': row['score'], 'cv_language': lang, 'existing': True}
    folder = paths.applications(f"{dt.date.today():%Y-%m-%d}_{slug(row['company'], 20)}_{slug(row['title'])}")
    folder.mkdir(parents=True, exist_ok=True)
    salary = ' '.join(str(x) for x in (row['salary_min'], row['salary_max'], row['salary_currency'], row['salary_period']) if x)
    (folder / 'job.md').write_text(
        f"# {row['title']} — {row['company']}\n\n"
        f"- id: {row['id']}\n- url: {row['url']}\n- source: {row['source']}\n- location: {row['location']}\n"
        f"- work_mode: {row['work_mode']}\n- salary: {salary or 'no publicado'}\n"
        f"- cv_language: {lang} ({lang_reason})  <- CV, carta y respuestas DEBEN ir en este idioma\n"
        f"- score: {row['score']} — {row['score_reason']}\n\n## Description\n\n{row['description'] or ''}\n",
        encoding='utf-8')
    rel = folder.relative_to(paths.user_dir()).as_posix()
    db.set_status(conn, row['id'], row['status'], note='application folder created', app_dir=rel)
    return {'id': row['id'], 'dir': rel, 'title': row['title'], 'company': row['company'], 'score': row['score'], 'cv_language': lang}


def apply_sources(config):
    """Sources whose postings we can actually apply to (search.yaml apply_sources; default: every configured source)."""
    return config.get('apply_sources') or list((config.get('sources') or {}).keys()) + ['mail']


def top(conn, config, min_score=None, limit=10):
    min_score = min_score if min_score is not None else (config.get('scoring') or {}).get('threshold_tailor', 50)
    sources = apply_sources(config)
    rows = conn.execute("SELECT * FROM jobs WHERE status='scored' AND app_dir IS NULL AND score>=? "
                        f"AND source IN ({','.join('?' * len(sources))}) ORDER BY score DESC LIMIT ?",
                        (min_score, *sources, limit)).fetchall()
    return [create(conn, r) for r in rows]


def one(conn, job_id):
    row = conn.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    if not row:
        raise ValueError(f'Unknown job: {job_id}')
    return create(conn, row)


def job_id_of(folder):
    match = re.search(r'^- id: (\S+)', (folder / 'job.md').read_text(encoding='utf-8'), re.M)
    if not match:
        raise ValueError(f'{folder}/job.md has no id')
    return match.group(1)


def resolve(folder):
    """Accept 'applications/x', 'x' or an absolute path."""
    from pathlib import Path
    folder = Path(folder)
    for candidate in (folder, paths.user(folder), paths.applications(folder)):
        if (candidate / 'job.md').exists():
            return candidate.resolve()
    raise FileNotFoundError(f'No job.md in {folder}')


def log_submission(conn, folder, status, channel, note='', agent='claude'):
    folder = resolve(folder)
    stamp = dt.datetime.now().astimezone().isoformat(timespec='seconds')
    with open(folder / 'submission.log', 'a', encoding='utf-8') as stream:
        stream.write(f"\nstatus: {status}\nchannel: {channel}\ntime: {stamp}\nnote: {note}\n")
    db.set_status(conn, job_id_of(folder), status, note=f'{channel} {note}'[:200], agent=agent)
    return folder
