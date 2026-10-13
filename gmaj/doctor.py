"""Environment checklist. Each item says what is wrong and the exact command to fix it on this OS.

The agent (INSTALL.md) runs `gmaj doctor --json`, asks the user before each fix, and checks the browser
extensions itself (Python cannot see them).
"""
import importlib.util
import json
import shutil
import subprocess
import sys

from . import engines, paths, render_cv, schedule, validate

WIN = sys.platform.startswith('win')
MAC = sys.platform == 'darwin'

FIX = {
    'git': 'winget install --id Git.Git -e' if WIN else 'xcode-select --install' if MAC else 'sudo apt install git',
    'uv': ('powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' if WIN
           else 'curl -LsSf https://astral.sh/uv/install.sh | sh'),
    'chrome': ('winget install --id Google.Chrome -e' if WIN else 'brew install --cask google-chrome  (o descarga https://www.google.com/chrome/)'
               if MAC else 'instala Google Chrome desde https://www.google.com/chrome/'),
    'claude': ('powershell -c "irm https://claude.ai/install.ps1 | iex"' if WIN else 'curl -fsSL https://claude.ai/install.sh | bash'),
    'codex': ('npm install -g @openai/codex  (requiere Node: winget install --id OpenJS.NodeJS.LTS -e)' if WIN
              else 'brew install codex  (o npm install -g @openai/codex)'),
    'deps': 'uv sync',
}
DEPS = ('yaml', 'requests', 'bs4', 'feedparser', 'markdown')


def item(name, ok, detail='', fix=None, required=True):
    return {'check': name, 'ok': bool(ok), 'required': required, 'detail': detail, 'fix': None if ok else fix}


def engine_mode():
    try:
        return engines.load().get('mode')
    except Exception:
        return None


def checks():
    out = [item('python>=3.11', sys.version_info >= (3, 11), sys.version.split()[0], FIX['uv'])]
    missing = [d for d in DEPS if importlib.util.find_spec(d) is None]
    out.append(item('dependencias', not missing, ', '.join(missing) or 'ok', FIX['deps']))
    out.append(item('git', shutil.which('git'), shutil.which('git') or 'no encontrado', FIX['git']))
    out.append(item('uv', shutil.which('uv'), shutil.which('uv') or 'no encontrado', FIX['uv'], required=False))
    browser = render_cv.find_browser()
    out.append(item('navegador para PDF (Chrome/Edge)', browser, browser or 'no encontrado', FIX['chrome']))
    mode = engine_mode()
    for name in engines.ENGINES:
        needed = mode in (name, 'dual')
        found = engines.binary(name)
        detail = found or ('no encontrado' + ('' if needed else ' (no se usa en este modo)'))
        out.append(item(f'CLI de {name}', found, detail, FIX[name], required=needed))
    out.append(item('engines.yaml', mode, mode or 'falta: elige claude, codex o dual (`gmaj engines set <modo>`)',
                    'gmaj engines set claude'))
    ignored = subprocess.run(['git', 'check-ignore', '-q', 'user/profile.yaml'], cwd=paths.ROOT).returncode == 0 if shutil.which('git') else True
    out.append(item('user/ fuera de git', ignored, 'user/ está en .gitignore' if ignored else 'PELIGRO: user/ se versionaría',
                    'agrega "user/" a .gitignore'))
    v = validate.check()
    out.append(item('perfil completo (gmaj validate)', v['ok'], '; '.join(v['problems'][:5]) or 'ok',
                    'continúa la entrevista (skill gmaj-onboarding)', required=False))
    out.append(item('tarea diaria de descubrimiento', schedule.status('discover'), '', 'gmaj schedule install --time 08:30',
                    required=False))
    return out


def main(as_json=False):
    results = checks()
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        for r in results:
            mark = 'OK ' if r['ok'] else ('ERR' if r['required'] else '-- ')
            print(f"[{mark}] {r['check']}: {r['detail']}" + (f"\n      arreglo: {r['fix']}" if r['fix'] else ''))
    return 0 if all(r['ok'] or not r['required'] for r in results) else 1
