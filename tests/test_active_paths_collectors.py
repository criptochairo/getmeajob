import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import load_config
from gmaj import add_job, cli, config, db, doctor, engines, paths, pipeline, prefilter, schedule, tools, validate


@pytest.mark.parametrize('options', [False, {},
                                     {'enabled': False, 'browser': True}, {'enabled': 1, 'browser': True}])
def test_sources_require_explicit_enabled(options, monkeypatch):
    cfg = {'sources': {'occ': options}}
    monkeypatch.setattr(config, 'search', lambda: cfg)
    assert config.active_sources(cfg) == {}
    assert not pipeline.enabled(cfg, 'occ')
    with pytest.raises(ValueError):
        tools.collector('occ')


def test_active_browser_list_and_collectors_share_filter(monkeypatch):
    cfg = load_config()
    cfg['sources']['occ'] = {'enabled': True, 'browser': True}
    cfg['sources']['indeed'] = {'enabled': True}
    monkeypatch.setattr(config, 'search', lambda: cfg)
    assert list(config.active_sources(cfg, browser=True)) == ['occ']
    assert 'const QUERIES' in tools.collector('occ')
    with pytest.raises(ValueError):
        tools.collector('indeed')


@pytest.mark.parametrize('options', [True, {'browser': True}, {'enabled': True, 'browser': True}])
def test_legacy_and_implicit_sources_are_active(options):
    cfg = {'sources': {'occ': options}}
    assert 'occ' in config.active_sources(cfg)
    assert pipeline.enabled(cfg, 'occ')
    assert bool(config.active_sources(cfg, browser=True)) == isinstance(options, dict)


def test_scalar_source_reaches_fetcher_as_options(monkeypatch):
    cfg = load_config()
    cfg['sources'] = {'remotive': True}
    received = []
    class Module:
        @staticmethod
        def fetch(config, client):
            received.append(config['sources']['remotive'])
            return []
    monkeypatch.setattr(pipeline.importlib, 'import_module', lambda name: Module)
    result = pipeline.fetch(db.connect(), cfg)
    assert received == [{'enabled': True}]
    assert result['sources']['remotive']['errors'] == []


def test_browser_disabled_sources_are_visible(user_dir, monkeypatch, capsys):
    cfg = load_config()
    cfg['sources']['occ'] = {'enabled': False, 'browser': True}
    cfg['sources']['indeed'] = {'browser': True}
    (user_dir / 'search.yaml').write_text(yaml.safe_dump(cfg), encoding='utf-8')
    cli.main(['sources', '--browser'])
    output = json.loads(capsys.readouterr().out)
    assert 'occ' in output['disabled_browser'] and 'occ' not in output['active']
    assert 'indeed' in output['active']
    assert any('OCC' in w and 'enabled: true' in w for w in validate.check()['warnings'])
    monkeypatch.setattr(schedule, 'status', lambda *a: False)
    assert any('OCC' in r['detail'] and 'enabled: true' in r['detail'] for r in doctor.checks())


def test_prompts_resolve_active_user_and_scheduled_command_captures_it(user_dir, monkeypatch):
    other = user_dir.parent / "second user 'test'"
    monkeypatch.setenv('GMAJ_USER_DIR', str(other))
    for name in ('tailor.md', 'review.md', 'score.md', 'apply.md', 'daily.md', 'mail_triage.md'):
        prompt = engines.prompt_file(name)
        assert other.as_posix() in prompt
        assert '`user/profile.yaml`' not in prompt
        assert prompt.count('Antes de leer skills') == (0 if name == 'score.md' else 1)
        assert 'Resuelve toda ruta' not in prompt
        if name == 'score.md':
            assert 'uv run gmaj paths' not in prompt
        else:
            assert 'toda ruta user/' in prompt
    assert paths.active()['profile.yaml'] == str(other / 'profile.yaml')
    args = schedule.args_for('daily')
    # Execute the actual bootstrap with a mocked run_module; never install a task.
    code = args[1].replace('runpy.run_module', 'capture')
    got = []
    exec(code, {'capture': lambda *a, **kw: got.append(os.environ['GMAJ_USER_DIR'])})
    assert got == [str(other)] and args[-1] == 'run-daily'


def test_windows_schedule_propagates_active_user(monkeypatch, user_dir):
    if os.name != 'nt':
        pytest.skip('Windows registration arguments')
    calls = []
    monkeypatch.setattr(schedule, 'status', lambda *a: True)
    def runner(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)
    assert schedule.install(runner=runner)[0]
    assert 'GMAJ_USER_DIR' in calls[0][-1]
    assert 'New-ScheduledTaskAction' in calls[0][-1]


def test_indeed_collector_preserves_lower_family_salary_through_prefilter(monkeypatch):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node needed to execute collector with a local browser mock')
    cfg = load_config()
    cfg['queries'] = {'data': ['Data Analyst']}
    cfg['sources']['indeed'] = {'enabled': True, 'browser': True, 'locations': ['Mexico']}
    cfg['salary']['floor_month'] = 30000
    cfg['salary']['role_families'] = [{'name': 'data', 'title_keywords': ['data analyst'], 'floor_month': 15000}]
    monkeypatch.setattr(config, 'search', lambda: cfg)
    template = tools.collector('indeed')
    item = {'jobkey': '1', 'title': 'Data Analyst', 'company': 'Example', 'formattedLocation': 'Mexico',
            'remoteLocation': True, 'salarySnippet': {'text': 'MXN 20,000 por mes'}, 'snippet': 'SQL'}
    mock = '''global.window = {}; global.location = {origin:'https://example.com'};
global.fetch = async () => ({ok:true, text:async () => 'window.mosaic.providerData["mosaic-provider-jobcards"]=' + JSON.stringify({metaData:{mosaicProviderJobCardsModel:{results:ITEMS}}}) + ';\\n'});
'''.replace('ITEMS', json.dumps([item]))
    code = mock + template + '\nsetImmediate(() => process.stdout.write(JSON.stringify(window.__indeed)));'
    result = subprocess.run([node, '-e', code], capture_output=True, text=True, check=True, timeout=10)
    items = json.loads(result.stdout)
    assert len(items) == 1 and 'MXN 20,000 por mes' in items[0]['description']
    conn = db.connect()
    assert add_job.insert(conn, items, cfg)['inserted'] == 1
    row = conn.execute('SELECT * FROM jobs').fetchone()
    assert (row['salary_min'], row['salary_currency'], row['salary_period']) == (20000, 'MXN', 'month')
    assert prefilter.evaluate(dict(row), cfg)[0] == 'filtered'
    assert '__FLOOR__' not in template
