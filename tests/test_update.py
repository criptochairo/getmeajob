import subprocess

from gmaj import update


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


def test_updated_runs_uv_sync_when_deps_change(monkeypatch):
    monkeypatch.setattr(update.tools, 'sync_skills', lambda: [])
    heads = iter(['true', 'aaa1111', 'bbb2222'])   # is-inside-work-tree, HEAD antes, HEAD después
    runner, calls = fake_git({'rev-parse': lambda: next(heads), 'diff': 'uv.lock\n', 'log': '- mejora\n'})
    r = update.auto(runner)
    assert r['status'] == 'updated' and 'mejora' in r['message']
    assert ['uv', 'sync', '--quiet'] in calls
