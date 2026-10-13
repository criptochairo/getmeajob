"""Render a Markdown CV/cover to an ATS-friendly single-column PDF with headless Chrome or Edge (Windows, macOS, Linux).

GMAJ_BROWSER overrides the browser executable. Page size: profile.yaml cv_policy.page_size (Letter | A4).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

CANDIDATES = {
    'win32': [r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe', r'%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe',
              r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe', r'%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe',
              r'%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe'],
    'darwin': ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
               '~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
               '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
               '/Applications/Chromium.app/Contents/MacOS/Chromium'],
}
ON_PATH = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome', 'msedge', 'microsoft-edge']

CSS = """
@page { size: %(page)s; margin: 14mm 16mm; }
body { font-family: Calibri, Carlito, "Helvetica Neue", Arial, sans-serif; font-size: 10.3pt; line-height: 1.32; color: #111; }
h1 { font-size: 19pt; margin: 0 0 2pt; }
h1 + p { margin: 0 0 8pt; }
h2 { font-size: 11.5pt; text-transform: uppercase; letter-spacing: .4pt; border-bottom: 1px solid #999;
     margin: 10pt 0 4pt; padding-bottom: 1pt; }
p { margin: 3pt 0; }
ul { margin: 2pt 0 5pt 15pt; padding: 0; }
li { margin: 1pt 0; }
a { color: #111; text-decoration: none; }
"""


def find_browser():
    if os.environ.get('GMAJ_BROWSER'):
        return os.environ['GMAJ_BROWSER']
    platform = 'win32' if sys.platform.startswith('win') else sys.platform
    for raw in CANDIDATES.get(platform, []):
        path = Path(os.path.expanduser(os.path.expandvars(raw)))
        if path.exists():
            return str(path)
    for name in ON_PATH:
        found = shutil.which(name)
        if found:
            return found
    return None


def page_size():
    try:
        from . import config
        return (config.profile().get('cv_policy') or {}).get('page_size', 'Letter')
    except Exception:
        return 'Letter'


def render(src, out=None, page=None):
    src = Path(src).resolve()
    out = Path(out).resolve() if out else src.with_suffix('.pdf')
    browser = find_browser()
    if not browser:
        raise RuntimeError('No encontré Chrome ni Edge. Instala Google Chrome o define GMAJ_BROWSER con la ruta del navegador.')
    # Python-Markdown needs a blank line before a list; our CVs put bullets right under the role line.
    lines, prev = [], ''
    for line in src.read_text(encoding='utf-8').splitlines():
        if line.startswith('- ') and prev.strip() and not prev.startswith('- '):
            lines.append('')
        lines.append(line)
        prev = line
    body = markdown.markdown('\n'.join(lines), extensions=['nl2br'])
    html = src.with_suffix('.html')
    css = CSS % {'page': page or page_size()}
    html.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>',
                    encoding='utf-8')
    try:
        subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={out}', html.as_uri()], check=True, capture_output=True, timeout=120)
    finally:
        html.unlink(missing_ok=True)
    return out
