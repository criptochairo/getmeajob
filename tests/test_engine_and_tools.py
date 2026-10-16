"""Engine adapter, validation, packages, collectors, skills mirror and scrub — all on the fictional persona."""
import json
import subprocess
import types

import pytest
import yaml

from gmaj import applications, check_package, db, engines, paths, scrub, tools, validate


def set_mode(user_dir, mode):
    path = user_dir / 'engines.yaml'
    cfg = yaml.safe_load(path.read_text(encoding='utf-8'))
    cfg['mode'] = mode
    path.write_text(yaml.safe_dump(cfg), encoding='utf-8')


def fake_runner(outputs, calls):
    def run(cmd, **kwargs):
        calls.append(cmd)
        out, code = outputs.pop(0)
        return types.SimpleNamespace(stdout=out, stderr='', returncode=code)
    return run


@pytest.mark.parametrize('mode,expected', [('claude', 'claude'), ('codex', 'codex')])
def test_single_engine_never_calls_the_other(user_dir, monkeypatch, mode, expected):
    set_mode(user_dir, mode)
    monkeypatch.setattr(engines, 'binary', lambda e: f'/bin/{e}')
    calls = []
    for role in engines.ROLES:
        r = engines.run(role, 'hola', runner=fake_runner([('ok', 0)], calls))
        assert r['engine'] == expected
    assert all(c[0] == f'/bin/{expected}' for c in calls)


def test_claude_and_codex_commands(user_dir, monkeypatch):
    monkeypatch.setattr(engines, 'binary', lambda e: e)
    cfg = engines.load()
    claude = engines.command('claude', engines.role_settings('score', 'claude', cfg), cfg, chrome=True)
    assert claude[:2] == ['claude', '-p'] and '--chrome' in claude and claude[claude.index('--model') + 1] == 'haiku'
    codex = engines.command('codex', engines.role_settings('review', 'codex', cfg), cfg)
    assert codex[:2] == ['codex', 'exec'] and codex[-1] == '-' and 'model_reasoning_effort="medium"' in codex


def test_dual_failover_on_limit(user_dir, monkeypatch):
    set_mode(user_dir, 'dual')
    monkeypatch.setattr(engines, 'binary', lambda e: e)
    calls = []
    r = engines.run('review', 'x', runner=fake_runner([('You have hit your usage limit', 1), ('done', 0)], calls))
    assert [c[0] for c in calls] == ['codex', 'claude']
    assert r['engine'] == 'claude' and r['failover_from'] == 'codex' and r['code'] == 0
    log = (user_dir / 'logs/usage.jsonl').read_text(encoding='utf-8').splitlines()
    assert json.loads(log[0])['limit_hit'] is True


def test_single_engine_limit_is_reported_not_failed_over(user_dir, monkeypatch):
    monkeypatch.setattr(engines, 'binary', lambda e: e)
    calls = []
    r = engines.run('tailor', 'x', runner=fake_runner([('Claude usage limit reached', 1)], calls))
    assert len(calls) == 1 and r['code'] == engines.LIMIT_EXIT


def test_validate_fixture_and_template(user_dir):
    assert validate.check()['ok'], validate.check()['problems']
    blank = validate.check(paths.ROOT / 'templates' / 'user')
    assert not blank['ok'] and any('personal.full_name' in p for p in blank['problems'])


def scored_job(conn, **extra):
    record = dict(source='linkedin_guest', external_id='9', url='https://example.com/9', title='Analista de datos',
                  company='Acme', description='Buscamos analista de datos con experiencia en SQL y Power BI para el equipo.')
    record.update(extra)
    db.insert_job(conn, record)
    ident = db.job_id(record)
    db.set_status(conn, ident, 'scored', 'fit', score=80, score_reason='fit')
    return ident


def test_top_is_idempotent(user_dir):
    from conftest import load_config
    conn = db.connect()
    scored_job(conn)
    first = applications.top(conn, load_config())
    second = applications.top(conn, load_config())
    assert len(first) == 1 and second == []
    assert first[0]['cv_language'] == 'es'
    assert len(list((user_dir / 'applications').iterdir())) == 1
    again = applications.one(conn, first[0]['id'])
    assert again.get('existing') and again['dir'] == first[0]['dir']



def test_top_skips_company_already_applied(user_dir):
    from conftest import load_config
    conn = db.connect()
    first = scored_job(conn)
    db.set_status(conn, first, 'applied', 'sent')
    again = scored_job(conn, source='computrabajo', external_id='10', url='https://example.com/10', title='Data Analyst', company='ACME ')
    assert applications.top(conn, load_config()) == []
    assert conn.execute('SELECT status FROM jobs WHERE id=?', (again,)).fetchone()['status'] == 'rejected'


def test_check_package_uses_profile_contact_and_forbidden(user_dir):
    from conftest import load_config
    conn = db.connect()
    scored_job(conn)
    folder = user_dir / applications.top(conn, load_config())[0]['dir']
    cv = (user_dir / 'variants/cv_datos_es.md').read_text(encoding='utf-8')
    (folder / 'cv.md').write_text(cv, encoding='utf-8')
    (folder / 'cover.md').write_text('Estimado equipo de Acme: me interesa la vacante de analista de datos con experiencia en SQL para el equipo.', encoding='utf-8')
    (folder / 'answers.json').write_text('{"cv_language": "es", "screening": []}', encoding='utf-8')
    assert check_package.check(folder)['ok'], check_package.check(folder)
    (folder / 'cv.md').write_text(cv.replace('55 0000 0000', '55 9999 9999') + '\n- Aumentó 75% las ventas del equipo.', encoding='utf-8')  # scrub:ok (ficticio)
    issues = ' '.join(check_package.check(folder)['issues'])
    assert 'forbidden "55 9999 9999"' in issues and 'contact missing' in issues and '75%' in issues  # scrub:ok


def test_log_submission(user_dir):
    from conftest import load_config
    conn = db.connect()
    ident = scored_job(conn)
    folder = applications.top(conn, load_config())[0]['dir']
    applications.log_submission(conn, folder, 'applied', 'linkedin', 'Easy Apply', agent='codex')
    row = conn.execute('SELECT status, assigned_agent FROM jobs WHERE id=?', (ident,)).fetchone()
    assert tuple(row) == ('applied', 'codex')
    from gmaj import pace
    assert pace.sent_today('linkedin') == 1


def test_collectors_render_user_values(user_dir):
    occ = tools.collector('occ')
    indeed = tools.collector('indeed')
    for js in (occ, indeed):
        assert '30000' in js
    assert '"analista-de-datos"' in occ and 'const QUERIES = __QUERIES__' not in occ
    assert '"data analyst"' in indeed and 'coyoac' in indeed.lower()
    assert '__HOME__' not in indeed and '__RELEVANT__' not in occ


def test_pace_first_week_cap():
    import datetime as dt
    from gmaj import pace
    limits = {'per_platform_per_day': {'default': 25}, 'first_week_per_day': 10, 'start_date': '2026-10-01', 'jitter_pct': 0}
    assert pace.cap(limits, 'linkedin', dt.date(2026, 10, 3)) == 10
    assert pace.cap(limits, 'linkedin', dt.date(2026, 10, 9)) == 25


def test_autonomy_offer(user_dir):
    for _ in range(9):
        assert not tools.record_approval()['offer_autopilot']
    tools.record_approval(clean=False)
    assert tools.record_approval()['offer_autopilot']
    assert tools.set_autonomy('autopilot')['autonomy'] == 'autopilot'


def test_skills_mirror_is_in_sync():
    assert tools.sync_skills(check_only=True) == []


def test_template_has_no_personal_data():
    findings = scrub.scan(terms=[])
    assert findings == []


def test_scrub_flags_patterns(tmp_path):
    f = tmp_path / 'x.md'
    f.write_text('mail me: someone@gmail.com\ncall 55 1234 5678\nok: ana@example.com\n', encoding='utf-8')  # scrub:ok
    found = scrub.scan([f], terms=['secreto'])
    kinds = {w.split(':')[0] for _, _, w in found}
    assert kinds == {'email', 'phone'}


def test_user_dir_is_gitignored():
    r = subprocess.run(['git', 'check-ignore', '-q', 'user/profile.yaml'], cwd=paths.ROOT)
    assert r.returncode == 0


def test_limit_text_in_successful_run_is_not_a_limit(user_dir, monkeypatch):
    monkeypatch.setattr(engines, 'binary', lambda e: e)
    calls = []
    r = engines.run('tailor', 'x', runner=fake_runner([('Nota: revisé el usage limit del plan', 0)], calls))
    assert r['code'] == 0 and not r['limit_hit']


def test_decimal_percent_backed_by_profile(user_dir):
    from conftest import load_config
    profile = user_dir / 'profile.yaml'
    profile.write_text(profile.read_text(encoding='utf-8') + '\n# logro: 12.5% de ahorro\n', encoding='utf-8')
    conn = db.connect()
    scored_job(conn)
    folder = user_dir / applications.top(conn, load_config())[0]['dir']
    cv = (user_dir / 'variants/cv_datos_es.md').read_text(encoding='utf-8') + '\n- Ahorro de 12.5% en costos del equipo.'
    (folder / 'cv.md').write_text(cv, encoding='utf-8')
    (folder / 'cover.md').write_text('Estimado equipo de Acme: me interesa la vacante de analista de datos con experiencia en SQL para el equipo.', encoding='utf-8')
    (folder / 'answers.json').write_text('{"cv_language": "es"}', encoding='utf-8')
    assert check_package.check(folder)['ok'], check_package.check(folder)


def test_top_respects_daily_tailor_cap_and_unique_folders(user_dir):
    from conftest import load_config
    cfg = load_config()
    cfg['limits']['tailor_per_day'] = 2
    conn = db.connect()
    for i in range(4):
        scored_job(conn, external_id=str(i), url=f'https://example.com/{i}', company=f'Acme {i}')
    assert len(applications.top(conn, cfg, limit=10)) == 2
    assert applications.top(conn, cfg, limit=10) == []
    dirs = [r[0] for r in conn.execute('SELECT app_dir FROM jobs WHERE app_dir IS NOT NULL')]
    assert len(set(dirs)) == 2 and all(d.rsplit('_', 1)[1] for d in dirs)
