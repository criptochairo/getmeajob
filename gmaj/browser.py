"""Make sure Chrome is open before an unattended run that needs the browser extension.

Claude in Chrome / Codex computer-use only connect to a running Chrome; a scheduled run at 9:30 with Chrome
closed would discover jobs but couldn't verify work mode or apply. `chrome_profile` in user/engines.yaml picks
the Chrome profile folder where the extension lives ("Profile 1", "Default"...); empty = Chrome's last used.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

WINDOWS_PATHS = [r'%ProgramFiles%\Google\Chrome\Application\chrome.exe',
                 r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe',
                 r'%LocalAppData%\Google\Chrome\Application\chrome.exe']


def running(runner=subprocess.run):
    if os.name == 'nt':
        out = runner(['tasklist', '/FI', 'IMAGENAME eq chrome.exe', '/NH'], capture_output=True, text=True).stdout or ''
        return 'chrome.exe' in out.lower()
    out = runner(['pgrep', '-x', 'Google Chrome'], capture_output=True, text=True)
    return out.returncode == 0


def ensure_chrome(profile='', wait=20, runner=subprocess.run, popen=subprocess.Popen, sleep=time.sleep):
    """Returns 'running', 'started' or 'not_found'."""
    if running(runner):
        return 'running'
    args = [f'--profile-directory={profile}'] if profile else []
    if os.name == 'nt':
        exe = next((p for p in (Path(os.path.expandvars(x)) for x in WINDOWS_PATHS) if p.exists()), None)
        if not exe:
            return 'not_found'
        popen([str(exe), *args])
    elif sys.platform == 'darwin':
        popen(['open', '-a', 'Google Chrome', '--args', *args])
    else:
        popen(['google-chrome', *args])
    sleep(wait)   # que cargue la extensión antes de conectar
    return 'started'
