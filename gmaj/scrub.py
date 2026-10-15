"""Scan the public template for personal data before publishing.

Generic patterns (emails, Mexican phones, CURP, RFC) always run. A private denylist (one term per line: names,
old phones, employers) is read from GMAJ_SCRUB_DENYLIST or ~/.gmaj-scrub-denylist.txt and is never versioned.
Mark an intentional line with `scrub:ok`.
"""
import os
import re
import subprocess
from pathlib import Path

from . import paths

TEXT = {'.md', '.yaml', '.yml', '.py', '.js', '.json', '.txt', '.toml', '.ini', '.cfg', '.html', '.ps1', '.sh'}
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
EMAIL_OK = re.compile(r'@(example\.(com|org|net)|ejemplo\.(com|mx)|anthropic\.com|users\.noreply\.github\.com)$', re.I)
FAKE_PHONES = {'5500000000', '5599999999'}   # números ficticios de la persona de prueba
PATTERNS = {
    'phone': re.compile(r'(?<![\d.])(?:\+?52[\s-]?)?(?:\d{2}[\s-]\d{4}[\s-]\d{4}|\d{10})(?![\d.])'),
    'curp': re.compile(r'\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b'),
    'rfc': re.compile(r'\b[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}\b'),
}


def denylist():
    path = Path(os.environ.get('GMAJ_SCRUB_DENYLIST') or Path.home() / '.gmaj-scrub-denylist.txt')
    if not path.exists():
        return []
    return [t.strip().lower() for t in path.read_text(encoding='utf-8').splitlines() if t.strip() and not t.startswith('#')]


def files():
    # -z: without it git quotes and escapes non-ASCII names ("CV Jos\303\251.md") and they would be skipped.
    listed = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=paths.ROOT,
                            capture_output=True, text=True, encoding='utf-8').stdout.split('\0')
    listed = [f for f in listed if f]
    return [paths.ROOT / f for f in listed]


def scan(targets=None, terms=None):
    terms = denylist() if terms is None else terms
    findings = []
    for path in targets if targets is not None else files():
        rel = path.relative_to(paths.ROOT).as_posix() if path.is_absolute() else str(path)
        if rel.startswith('user/'):
            findings.append((rel, 0, 'user/ no debe versionarse'))
            continue
        if path.suffix.lower() not in TEXT or not path.is_file():
            continue
        for n, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            if 'scrub:ok' in line:
                continue
            low = line.lower()
            findings += [(rel, n, f'denylist: {t}') for t in terms if t in low]
            findings += [(rel, n, f'email: {m}') for m in EMAIL.findall(line) if not EMAIL_OK.search(m)]
            findings += [(rel, n, f'{kind}: {m}') for kind, rx in PATTERNS.items() for m in rx.findall(line)
                         if not (kind == 'phone' and re.sub(r'\D', '', m)[-10:] in FAKE_PHONES)]
    return findings
