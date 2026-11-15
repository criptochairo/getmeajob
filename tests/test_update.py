import subprocess
import json
from pathlib import Path

import pytest

from gmaj import cli, config, update


@pytest.fixture(autouse=True)
def isolated_update(tmp_path, monkeypatch):
    monkeypatch.setattr(update.paths, 'ROOT', tmp_path)
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: [])


def fake_git(responses):
    calls = []
    def runner(cmd, **kwargs):
        calls.append(cmd)
        key = cmd[1] if cmd[0] == 'git' else cmd[0]
        out = responses.get(key, '')
        if callable(out):
            out = out()
        code, stdout = out if isinstance(out, tuple) else (0, out)
        return subprocess.CompletedProcess(cmd, code, stdout=stdout, stderr='boom' if code else '')
    return runner, calls


def test_skips_when_engine_files_were_edited():
    runner, calls = fake_git({'status': ' M gmaj/prefilter.py\n'})
    assert update.auto(runner)['status'] == 'skipped'
    assert not any(c[1] == 'pull' for c in calls)


def test_offline_never_raises():
    runner, _ = fake_git({'pull': (1, '')})
    assert update.auto(runner)['status'] == 'skipped'


def test_failed_pull_without_head_change_keeps_stderr_and_no_new_marker():
    runner, calls = fake_git({'pull': (1, ''), 'rev-parse': 'same'})
    assert update.auto(runner) == {'status': 'skipped', 'message': 'sin red o rama divergente: boom'}
    assert not (update.paths.ROOT / '.gmaj-sync-pending').exists()
    assert not any(c[0] == 'uv' for c in calls)


def test_sync_stops_after_three_failures():
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    marker.write_text('0')
    runner, calls = fake_git({'uv': (1, '')})
    for n in range(1, 4):
        update.auto(runner)
        assert marker.read_text() == str(n)
    assert 'uv sync' in update.auto(runner)['message']
    assert sum(c[0] == 'uv' for c in calls) == 3


def test_capped_sync_still_pulls_new_head(monkeypatch):
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    marker.write_text('3')
    skills = []
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: skills.append(True))
    runner, calls = updated_runner()
    result = update.auto(runner)
    assert result['status'] == 'updated'
    assert ['git', 'pull', '--ff-only', '--quiet'] in calls
    assert not any(c[0] == 'uv' for c in calls)
    assert marker.read_text() == '3'
    assert skills == [True]
    assert 'uv run gmaj update --sync-complete' in result['message']


def test_cli_sync_complete_clears_marker_only_after_skills_sync(monkeypatch, capsys):
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    marker.write_text('3')
    def fail():
        raise ValueError('copy failed')
    monkeypatch.setattr(update.tools, 'sync_skills', fail)
    with pytest.raises(SystemExit) as result:
        cli.main(['update', '--sync-complete'])
    assert result.value.code == 2
    assert marker.read_text() == '3'
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: [])
    cli.main(['update', '--sync-complete'])
    assert not marker.exists()
    assert 'Sincronizacion manual confirmada.' in capsys.readouterr().out


def test_pending_retry_and_new_update_only_sync_once():
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    marker.write_text('1')
    runner, calls = updated_runner()
    assert update.auto(runner)['status'] == 'updated'
    assert sum(c[0] == 'uv' for c in calls) == 1
    assert marker.exists()  # New dependencies wait until the next invocation.


def test_concurrent_marker_cleanup(monkeypatch):
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    marker.touch()
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: marker.unlink(missing_ok=True))
    runner, _ = fake_git({'rev-parse': 'same'})
    assert update.auto(runner)['status'] == 'current'


def test_updated_runs_uv_sync_when_deps_change(monkeypatch):
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: [])
    heads = iter(['true', 'aaa1111', 'bbb2222'])   # is-inside-work-tree, HEAD antes, HEAD después
    runner, calls = fake_git({'rev-parse': lambda: next(heads), 'diff': 'uv.lock\n', 'log': '- mejora\n'})
    r = update.auto(runner)
    assert r['status'] == 'updated' and 'mejora' in r['message']
    assert ['uv', 'sync', '--quiet'] in calls


def updated_runner(changed='uv.lock\n', **responses):
    heads = iter(['true', 'aaa1111', 'bbb2222'])
    return fake_git({'rev-parse': lambda: next(heads), 'diff': changed,
                     'log': '- mejora\n', **responses})


def test_current_does_not_sync():
    runner, calls = fake_git({'rev-parse': 'aaa1111'})
    assert update.auto(runner)['status'] == 'current'
    assert not (update.paths.ROOT / '.gmaj-sync-pending').exists()
    assert not any(c[0] == 'uv' for c in calls)


@pytest.mark.parametrize('updated', [False, True])
def test_update_does_not_warn_about_browser_portals(user_dir, updated):
    # OCC/Indeed con enabled: false y browser: true están activos por navegador:
    # la actualización no debe sugerir cambiar nada en search.yaml.
    (user_dir / 'search.yaml').write_text('''sources:
  occ: {browser: true, enabled: false}
  indeed: {browser: true, enabled: false}
''', encoding='utf-8')
    runner, _ = updated_runner() if updated else fake_git({'rev-parse': 'same'})
    result = update.auto(runner)
    assert result['status'] == ('updated' if updated else 'current')
    assert 'search.yaml' not in result['message']
    assert 'OCC' not in result['message'] and 'INDEED' not in result['message']


@pytest.mark.parametrize('updated', [False, True])
def test_update_without_search_config(user_dir, updated):
    (user_dir / 'search.yaml').unlink()
    runner, _ = updated_runner() if updated else fake_git({'rev-parse': 'same'})
    result = update.auto(runner)
    assert result['status'] == ('updated' if updated else 'current')
    assert 'search.yaml' not in result['message']


@pytest.mark.parametrize('failure', ['exit', 'timeout', 'missing', 'skills'])
def test_failed_sync_is_retried_even_without_head_change(monkeypatch, failure):
    runner, calls = updated_runner()
    def failing_runner(cmd, **kwargs):
        if cmd[0] == 'uv':
            if failure == 'exit':
                return subprocess.CompletedProcess(cmd, 1)
            if failure == 'timeout':
                raise subprocess.TimeoutExpired(cmd, kwargs['timeout'])
            if failure == 'missing':
                raise FileNotFoundError('uv')
        return runner(cmd, **kwargs)
    if failure == 'skills':
        def failed_skills():
            raise OSError('copy failed')
        monkeypatch.setattr(update.tools, 'sync_skills', failed_skills)
    result = update.auto(failing_runner)
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    assert result['status'] == 'updated'
    assert 'actualizado; sincronización pendiente' in result['message']
    assert marker.exists()
    synced = []
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: synced.append(True))
    retry, retry_calls = fake_git({'rev-parse': 'bbb2222'})
    assert update.auto(retry)['status'] == 'current'
    assert retry_calls[0] == ['uv', 'sync', '--quiet']
    assert synced == [True]
    assert not marker.exists()


def test_pending_sync_retries_before_dirty_check_and_offline_pull():
    marker = update.paths.ROOT / '.gmaj-sync-pending'
    marker.touch()
    runner, calls = fake_git({'status': ' M .claude/skills/example/SKILL.md'})
    assert update.auto(runner)['status'] == 'skipped'
    assert calls[0] == ['uv', 'sync', '--quiet']
    assert not marker.exists()


@pytest.mark.parametrize('command', ['status', 'diff', 'log'])
def test_git_failures_do_not_escape_and_return_truthful_status(command):
    runner, _ = updated_runner(**{command: (1, '')})
    result = update.auto(runner)
    assert result['status'] == ('skipped' if command == 'status' else 'updated')
    assert (update.paths.ROOT / '.gmaj-sync-pending').exists() == (command == 'diff')


@pytest.mark.parametrize('command', ['diff', 'log'])
def test_post_pull_timeouts_do_not_escape(command):
    runner, _ = updated_runner()
    def timeout(cmd, **kwargs):
        if cmd[:2] == ['git', command]:
            raise subprocess.TimeoutExpired(cmd, kwargs['timeout'])
        return runner(cmd, **kwargs)
    assert update.auto(timeout)['status'] == 'updated'


def test_skills_only_update_does_not_sync_dependencies(monkeypatch):
    synced = []
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: synced.append(True))
    runner, calls = updated_runner('.agents/skills/gmaj-daily/SKILL.md')
    assert update.auto(runner)['status'] == 'updated'
    assert synced == [True]
    assert not any(c[0] == 'uv' for c in calls)


def test_hook_allows_retry_and_update_syncs():
    root = Path(__file__).resolve().parents[1]
    settings = json.loads((root / '.claude/settings.json').read_text(encoding='utf-8'))
    timeout = settings['hooks']['SessionStart'][0]['hooks'][0]['timeout']
    assert timeout > update.SYNC_TIMEOUT + 8 * update.TIMEOUT
