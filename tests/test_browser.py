from types import SimpleNamespace

from gmaj import browser


def test_ensure_chrome_skips_when_running(monkeypatch):
    monkeypatch.setattr(browser, 'running', lambda runner=None: True)
    assert browser.ensure_chrome(popen=lambda *a: (_ for _ in ()).throw(AssertionError('no launch'))) == 'running'


def test_ensure_chrome_launches_profile(monkeypatch, tmp_path):
    exe = tmp_path / 'chrome.exe'
    exe.write_text('')
    monkeypatch.setattr(browser, 'running', lambda runner=None: False)
    monkeypatch.setattr(browser.os, 'name', 'nt')
    monkeypatch.setattr(browser, 'WINDOWS_PATHS', [str(exe)])
    launched = []
    assert browser.ensure_chrome('Profile 1', popen=launched.append, sleep=lambda s: None) == 'started'
    assert launched == [[str(exe), '--profile-directory=Profile 1']]
