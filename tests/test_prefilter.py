import json

import pytest

from conftest import load_config
from gmaj import cli, db, prefilter
from gmaj.fetchers.common import salary
from gmaj.fetchers.linkedin_guest import parse_cards

@pytest.mark.parametrize('changes,expected', [
    ({'description': 'Must be authorized to work in the United States'}, 'discarded'),
    ({'location': 'Remote - LATAM'}, 'filtered'),
    ({'salary_min': 6, 'salary_currency': 'USD', 'salary_period': 'hour'}, 'discarded'),
    ({'work_mode': 'hybrid', 'salary_min': 40000, 'salary_currency': 'MXN', 'salary_period': 'month'}, 'discarded'),
    ({'title': 'Data Intern'}, 'discarded'),
    ({}, 'filtered'),
    ({'work_mode': 'hybrid', 'location': 'Mexico City, Mexico', 'salary_min': 60000, 'salary_currency': 'MXN', 'salary_period': 'month'}, 'filtered'),
    ({'work_mode': 'hybrid', 'location': 'Santa Fe, Mexico City, Mexico'}, 'discarded'),
    ({'work_mode': 'hybrid', 'location': 'Polanco, Mexico City, Mexico'}, 'needs_user'),
    ({'work_mode': 'hybrid', 'location': 'Mexico City, Mexico', 'salary_min': 40000, 'salary_currency': 'MXN', 'salary_period': 'month'}, 'discarded'),
    ({'work_mode': 'hybrid'}, 'discarded'),
    ({'work_mode': 'onsite'}, 'discarded'),
    ({'description': 'US work authorization required. Remote LATAM applicants welcome'}, 'filtered'),
    ({'description': 'US work authorization required. Contractor role'}, 'discarded'),
    ({'description': 'No visa sponsorship. Remote Mexico'}, 'filtered'),
    ({'description': 'No visa sponsorship. Must reside in the United States'}, 'discarded'),
    ({'title': 'International Data Specialist'}, 'filtered'),
    ({'salary_min': 24000, 'salary_currency': 'USD', 'salary_period': 'year'}, 'filtered'),
    ({'description': 'Experience with Tableau is required'}, 'discarded'),
    ({'description': 'Our team uses Tableau internally'}, 'filtered'),
    ({'description': 'CPA required'}, 'discarded'),
    ({'description': 'Must be licensed in New York'}, 'discarded'),
    ({'description': 'No experience needed, we train you'}, 'discarded'),
    ({'description': 'Minimum of 10 years of experience'}, 'filtered'),   # years never discard outside entry_level
    ({'description': '10-15 years of experience in analytics'}, 'filtered'),
])
def test_rules(changes, expected):
    job = dict(title='Data Analyst', company='Example', work_mode='remote', description='', location='', salary_min=None)
    job.update(changes)
    assert prefilter.evaluate(job, load_config())[0] == expected

def test_dedupe_and_history(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    job = dict(source='a', external_id='1', url='https://example.com/1?utm_source=a', title='Data Analyst', company='Acme, Inc.', work_mode='remote')
    assert db.insert_job(conn, job)
    ident = db.job_id(job)
    db.set_status(conn, ident, 'approved', 'Reviewed', agent='claude')
    assert not db.insert_job(conn, {**job, 'source': 'b', 'external_id': '2', 'url': 'https://other.com/2', 'company': 'ACME INC', 'title': 'data analyst'})
    assert not db.insert_job(conn, {**job, 'external_id': '3', 'url': 'https://example.com/1?utm_source=b'})
    assert conn.execute('SELECT status FROM jobs').fetchone()[0] == 'approved'
    assert [r[0] for r in conn.execute('SELECT status FROM events')] == ['new', 'approved']
    assert prefilter.run(conn, load_config()) == {}
    with pytest.raises(ValueError):
        db.set_status(conn, ident, 'invalid')
    conn.close()

def test_refresh_only_updates_new_metadata(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    record = dict(source='test', external_id='1', url='https://example.com/1', title='Data Analyst', company='Acme', description='Old')
    assert db.insert_job(conn, record)
    assert not db.insert_job(conn, {**record, 'description': 'Updated', 'salary_min': 40000})
    assert conn.execute('SELECT description,salary_min FROM jobs').fetchone()[:] == ('Updated', 40000)
    ident = db.job_id(record)
    db.set_status(conn, ident, 'filtered', 'Passed')
    assert not db.insert_job(conn, {**record, 'description': 'Later', 'salary_min': 1})
    assert conn.execute('SELECT description,salary_min FROM jobs').fetchone()[:] == ('Updated', 40000)
    assert conn.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 2
    conn.close()

@pytest.mark.parametrize('text,expected', [
    ('USD 60,000 - 80,000 per year', (60000, 80000, 'USD', 'year')),
    ('MXN 30,000–40,000 mensual', (30000, 40000, 'MXN', 'month')),
    ('US$6/hour', (6, None, 'USD', 'hour')),
    ('$6/hour', (6, None, None, 'hour')),
    ('USD 80k - 120k annually', (80000, 120000, 'USD', 'year')),
])
def test_salary(text, expected):
    assert tuple(salary(text).values()) == expected

def test_linkedin_cards():
    html = '<div class="base-card" data-entity-urn="urn:li:jobPosting:123"><a class="base-card__full-link" href="https://linkedin.com/jobs/view/role-123?trk=foo"></a><h3 class="base-search-card__title">Legal Analyst</h3><h4 class="base-search-card__subtitle">Acme</h4><span class="job-search-card__location">Mexico</span></div>'
    assert list(parse_cards(html))[0]['external_id'] == '123'

def test_prefilter_records_reasons_and_is_idempotent(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    for ident, mode in [('1', 'remote'), ('2', 'onsite')]:
        db.insert_job(conn, dict(source='test', external_id=ident, url=f'https://example.com/{ident}',
                                title='Data Analyst ' + ident, company='Acme', work_mode=mode))
    assert prefilter.run(conn, load_config()) == {'filtered': 1, 'discarded': 1}
    assert all(r[0] for r in conn.execute('SELECT filter_reason FROM jobs'))
    assert conn.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 4
    assert prefilter.run(conn, load_config()) == {}
    assert conn.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 4
    conn.close()

def test_cli_agent_score_and_json(capsys):
    conn = db.connect()
    record = dict(source='test', external_id='1', url='https://example.com/1',
                  title='Data Analyst', company='Acme', description='a' * 5000)
    db.insert_job(conn, record)
    ident = db.job_id(record)
    conn.close()
    cli.main(['set-score', ident, '80', '--reason', 'Role fit'])
    cli.main(['set-status', ident, 'approved', '--note', 'Reviewed', '--agent', 'claude', '--app-dir', 'applications/example'])
    capsys.readouterr()
    cli.main(['list', '--status', 'approved', '--json'])
    result = json.loads(capsys.readouterr().out)
    assert len(result[0]['description']) == 4000
    conn = db.connect()
    row = conn.execute('SELECT * FROM jobs').fetchone()
    assert (row['score'], row['score_reason'], row['assigned_agent'], row['app_dir']) == (80, 'Role fit', 'claude', 'applications/example')
    assert [r[0] for r in conn.execute('SELECT status FROM events')] == ['new', 'scored', 'approved']
    conn.close()


def test_foreign_language_discarded():
    config = load_config()
    pt = {'title': 'Especialista de Compliance', 'description': 'Você vai atuar com conhecimento em regulação. Não exige inglês.', 'work_mode': 'remote'}
    es = {'title': 'Analista de Cumplimiento', 'description': 'Experiencia en regulatorio, beneficios de ley, remoto LATAM.', 'work_mode': 'remote'}
    assert prefilter.evaluate(pt, config)[0] == 'discarded'
    assert prefilter.evaluate(es, config)[0] == 'filtered'


def test_remote_flag_overridden_by_text():
    assert prefilter.actual_work_mode({'work_mode': 'remote', 'description': 'Esquema híbrido, 3 días en oficina en Monterrey.'}) == 'hybrid'
    assert prefilter.actual_work_mode({'work_mode': 'remote', 'description': 'This role is on-site in our Mexico City office.'}) == 'onsite'
    assert prefilter.actual_work_mode({'work_mode': 'remote', 'description': 'Fully remote role across LATAM.'}) == 'remote'


def test_title_key_merges_location_suffixes(tmp_path):
    conn = db.connect(tmp_path / 'jobs.db')
    base = dict(source='a', company='Acme', work_mode='remote')
    assert db.insert_job(conn, {**base, 'external_id': '1', 'url': 'https://x.com/1', 'title': 'Paralegal - Remote, Mexico'})
    assert not db.insert_job(conn, {**base, 'external_id': '2', 'url': 'https://x.com/2', 'title': 'Paralegal (CDMX)'})
    assert db.insert_job(conn, {**base, 'external_id': '3', 'url': 'https://x.com/3', 'title': 'Legal Counsel - Privacy'})
    assert db.insert_job(conn, {**base, 'external_id': '4', 'url': 'https://x.com/4', 'title': 'Legal Counsel - Employment'})


def test_office_policies():
    config = load_config()
    job = dict(title='Data Analyst', company='X', work_mode='onsite', description='', location='Coyoacán, Ciudad de México')
    assert prefilter.evaluate(job, config)[0] == 'discarded'
    config['work_mode']['onsite'] = 'zones'
    assert prefilter.evaluate(job, config)[0] == 'filtered'
    config['work_mode']['onsite'] = 'accept'
    assert prefilter.evaluate({**job, 'location': 'Monterrey'}, config)[0] == 'discarded'   # location_ok still applies
    assert prefilter.evaluate({**job, 'location': 'Monterrey, Mexico'}, config)[0] == 'filtered'


def test_salary_in_other_base_currency():
    config = load_config()
    config['currency'] = {'base': 'COP', 'rates': {'USD': 4000}}
    config['salary']['floor_month'] = 4_000_000
    job = dict(title='Data Analyst', company='X', work_mode='remote', description='', location='', salary_min=900,
               salary_currency='USD', salary_period='month')
    assert prefilter.evaluate(job, config)[0] == 'discarded'
    assert prefilter.evaluate({**job, 'salary_min': 1200}, config)[0] == 'filtered'
