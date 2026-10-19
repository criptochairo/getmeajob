"""Regressions found in the pre-release review (Claude + Codex)."""
import json
from datetime import date

from conftest import load_config
from test_linkedin_cooldown import Response, blocked_error
from gmaj import add_job, check_package, cooldown, db, prefilter, scrub
from gmaj.fetchers import linkedin_guest
from gmaj.fetchers.common import Client


def test_overlapping_jobs_count_once_and_years_round_down():
    today = date(2026, 10, 1)
    jobs = [{'start': '2020-01', 'end': '2022-01'}, {'start': '2021-01', 'end': '2022-01'}]
    assert check_package.experience_months(jobs, today) == 24
    assert check_package.claim_limits({'experience': [{'start': '2026-08', 'end': '2026-09'}]})['max_years'] == 0
    limits = check_package.claim_limits({'experience': jobs})
    assert limits['max_years'] == 2
    assert check_package.claim_issues('cv.md', '3 años de experiencia', limits)


def test_same_title_elsewhere_is_kept_after_a_discard(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    base = dict(source='linkedin_guest', title='Data Analyst', company='Acme')
    assert db.insert_job(conn, {**base, 'external_id': '1', 'url': 'https://x/1', 'location': 'New York, US'})
    db.set_status(conn, db.job_id({**base, 'external_id': '1'}), 'discarded', 'US only')
    assert db.insert_job(conn, {**base, 'external_id': '2', 'url': 'https://x/2', 'location': 'Mexico City, Mexico'})
    # Once a copy passed the filters, later reposts (any location) are skipped at insert time.
    db.set_status(conn, db.job_id({**base, 'external_id': '2'}), 'filtered', 'ok')
    assert not db.insert_job(conn, {**base, 'external_id': '3', 'url': 'https://x/3', 'location': 'CDMX'})


def test_old_unique_index_is_dropped(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    conn.execute("CREATE UNIQUE INDEX jobs_company_title ON jobs(company_key,title_key)")
    conn.close()
    conn = db.connect(tmp_path / 'jobs.db')
    names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")]
    assert 'jobs_company_title' not in names


def test_add_jobs_reads_salary_from_description(tmp_path):
    leads = tmp_path / 'leads.json'
    leads.write_text(json.dumps([{'source': 'mail', 'external_id': 'a1', 'url': 'https://x/a1', 'title': 'Data Analyst',
                                  'company': 'Acme', 'description': 'Sueldo MXN 10,000 mensual', 'force': True}]), encoding='utf-8')
    conn = db.connect()
    add_job.insert(conn, add_job.load(leads), load_config())
    row = conn.execute('SELECT salary_min FROM jobs').fetchone()
    assert row['salary_min'] == 10000


def test_remote_reject_is_honoured():
    config = load_config()
    config['work_mode']['remote'] = 'reject'
    job = dict(title='Data Analyst', company='Example', work_mode='remote', description='', location='', salary_min=None)
    assert prefilter.evaluate(job, config)[0] == 'discarded'


def test_prefilter_stores_mode_read_from_text(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    job = dict(source='a', external_id='1', url='https://x/1', title='Data Analyst', company='Acme', work_mode='remote',
               description='Esquema híbrido, 3 días en oficina')
    db.insert_job(conn, job)
    prefilter.run(conn, load_config())
    assert conn.execute('SELECT work_mode FROM jobs').fetchone()['work_mode'] == 'hybrid'


def test_linkedin_detail_blocks_start_cooldown(monkeypatch):
    client = Client('linkedin_guest', {'url': 'https://search.example', 'pause_on_block_seconds': 0, 'max_consecutive_blocks': 2,
                                       'or_group_size': 1, 'cooldown_hours': 3})
    monkeypatch.setattr(linkedin_guest, 'parse_cards', lambda html: [
        {'external_id': str(i), 'title': 'Data Analyst', 'company': 'Acme', 'url': f'https://x/{i}', 'location': 'Mexico'} for i in range(3)])
    monkeypatch.setattr(linkedin_guest, 'relevant', lambda title, config: True)

    def get(url, **kwargs):
        if 'jobPosting' in url:
            raise blocked_error()
        return Response('<li>card</li>')
    monkeypatch.setattr(client, 'get', get)
    list(linkedin_guest.fetch(load_config(), client))
    assert cooldown.active('linkedin_guest')


def test_linkedin_hybrid_regex_has_word_boundaries():
    source = open(linkedin_guest.__file__, encoding='utf-8').read()
    assert '\x08' not in source and r"r'\bhybrid\b'" in source


def test_scrub_lists_non_ascii_file_names(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return type('R', (), {'stdout': 'README.md\0docs/CV José.md\0'})()
    monkeypatch.setattr(scrub.subprocess, 'run', fake_run)
    names = [p.name for p in scrub.files()]
    assert '-z' in calls[0] and 'CV José.md' in names


def test_same_batch_keeps_the_eligible_copy_and_dedupes_after_filtering(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    base = dict(source='linkedin_guest', title='Data Analyst', company='Acme', work_mode='remote', description='')
    db.insert_job(conn, {**base, 'external_id': '1', 'url': 'https://x/1', 'location': 'New York, United States', 'work_mode': 'unknown'})
    db.insert_job(conn, {**base, 'external_id': '2', 'url': 'https://x/2', 'location': 'Mexico City, Mexico'})
    db.insert_job(conn, {**base, 'external_id': '3', 'url': 'https://x/3', 'location': 'Remote - LATAM'})
    prefilter.run(conn, load_config())
    status = {r['location']: r['status'] for r in conn.execute('SELECT location,status FROM jobs')}
    assert status['New York, United States'] == 'discarded'
    assert sorted(status.values()).count('filtered') == 1   # Mexico and LATAM are the same job: only one survives


def test_twins_come_back_when_the_kept_copy_is_discarded_later(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    base = dict(source='linkedin_guest', title='Data Analyst', company='Acme', work_mode='remote', description='')
    for ident, place in (('1', 'Mexico City, Mexico'), ('2', 'Remote - LATAM')):
        db.insert_job(conn, {**base, 'external_id': ident, 'url': f'https://x/{ident}', 'location': place})
    prefilter.run(conn, load_config())
    kept = conn.execute("SELECT id FROM jobs WHERE status='filtered'").fetchone()['id']
    db.set_status(conn, kept, 'scored', 'fit', score=80)
    db.set_status(conn, kept, 'discarded', 'hybrid when checked in the browser')
    assert prefilter.run(conn, load_config()) == {'filtered': 1}
