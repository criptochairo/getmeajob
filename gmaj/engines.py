"""Engine adapter: run one pipeline role (score, tailor, review, ...) as a fresh headless call to Claude or Codex.

user/engines.yaml:
  mode: claude | codex | dual
  assign: {role: claude|codex}        # only used in dual mode
  roles: {role: {claude: {model, effort}, codex: {model, effort}}}

Every call is a separate process with a clean context, so "whoever tailors never approves" holds even with one engine.
In dual mode, if the assigned engine hits its usage limit the call is retried once on the other engine.
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import config, paths

ENGINES = ('claude', 'codex')
ROLES = ('orchestrate', 'score', 'tailor', 'tailor_high', 'review', 'apply', 'mail', 'profile')
LIMIT_RE = re.compile(r'usage limit|rate limit|quota|limit reached|hit your limit|5-hour limit', re.I)
LIMIT_EXIT = 75

DEFAULTS = {
    'orchestrate': {'claude': {'model': 'sonnet', 'effort': 'medium'}, 'codex': {'model': None, 'effort': 'medium'}},
    'score':       {'claude': {'model': 'haiku', 'effort': 'low'}, 'codex': {'model': None, 'effort': 'low'}},
    'tailor':      {'claude': {'model': 'sonnet', 'effort': 'medium'}, 'codex': {'model': None, 'effort': 'medium'}},
    'tailor_high': {'claude': {'model': 'opus', 'effort': 'medium'}, 'codex': {'model': None, 'effort': 'high'}},
    'review':      {'claude': {'model': 'opus', 'effort': 'medium'}, 'codex': {'model': None, 'effort': 'medium'}},
    'apply':       {'claude': {'model': 'sonnet', 'effort': 'medium'}, 'codex': {'model': None, 'effort': 'medium'}},
    'mail':        {'claude': {'model': 'haiku', 'effort': 'low'}, 'codex': {'model': None, 'effort': 'low'}},
    'profile':     {'claude': {'model': 'opus', 'effort': 'medium'}, 'codex': {'model': None, 'effort': 'high'}},
}
DUAL_ASSIGN = {'orchestrate': 'claude', 'score': 'claude', 'tailor': 'claude', 'tailor_high': 'claude',
               'review': 'codex', 'apply': 'codex', 'mail': 'codex', 'profile': 'claude'}


def binary(engine):
    """Locate the CLI. Desktop-app users may not have it on PATH; doctor reports that."""
    found = shutil.which(engine)
    if found:
        return found
    home = Path.home()
    extra = {
        'claude': [home / '.local/bin/claude.exe', home / '.local/bin/claude', home / '.claude/local/claude',
                   Path(os.environ.get('APPDATA', '')) / 'npm/claude.cmd'],
        'codex': [Path(os.environ.get('APPDATA', '')) / 'npm/codex.cmd', home / '.local/bin/codex', Path('/opt/homebrew/bin/codex')],
    }[engine]
    for path in extra:
        if path.is_file():
            return str(path)
    return None


def load():
    cfg = config.engines()
    mode = cfg.get('mode')
    if mode not in ENGINES + ('dual',):
        raise ValueError(f'engines.yaml: mode must be claude, codex or dual (got {mode!r})')
    return cfg


def engine_for(role, cfg):
    if cfg['mode'] in ENGINES:
        return cfg['mode']
    return (cfg.get('assign') or {}).get(role) or DUAL_ASSIGN.get(role, 'claude')


def role_settings(role, engine, cfg):
    settings = dict(DEFAULTS.get(role, DEFAULTS['tailor'])[engine])
    settings.update(((cfg.get('roles') or {}).get(role) or {}).get(engine) or {})
    return settings


def command(engine, settings, cfg, chrome=False, last_message=None):
    exe = binary(engine)
    if not exe:
        raise FileNotFoundError(f'No encontré el CLI de {engine}. Corre `gmaj doctor`.')
    if engine == 'claude':
        cmd = [exe, '-p', '--permission-mode', cfg.get('claude_permission_mode', 'auto')]
        if settings.get('model'):
            cmd += ['--model', settings['model']]
        if settings.get('effort'):
            cmd += ['--effort', settings['effort']]
        if chrome:
            cmd.append('--chrome')
        return cmd
    cmd = [exe, 'exec', '-s', cfg.get('codex_sandbox', 'workspace-write')]
    if settings.get('model'):
        cmd += ['-m', settings['model']]
    if settings.get('effort'):
        cmd += ['-c', f'model_reasoning_effort="{settings["effort"]}"']
    if last_message:
        cmd += ['--output-last-message', str(last_message)]
    return cmd + ['-']


def log_usage(entry):
    path = paths.user('logs', 'usage.jsonl')
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + '\n')


def run_once(engine, role, prompt, cfg, chrome=False, timeout=None, runner=subprocess.run):
    settings = role_settings(role, engine, cfg)
    last = paths.user('logs', f'last_{role}_{engine}.md')
    last.parent.mkdir(parents=True, exist_ok=True)
    cmd = command(engine, settings, cfg, chrome=chrome, last_message=last if engine == 'codex' else None)
    start = time.monotonic()
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    try:
        proc = runner(cmd, input=prompt, text=True, encoding='utf-8', errors='replace', capture_output=True,
                      cwd=paths.ROOT, timeout=timeout, env=env)
        output, code = (proc.stdout or '') + (proc.stderr or ''), proc.returncode
    except subprocess.TimeoutExpired as exc:
        output, code = str(exc.stdout or '') + '\nTIMEOUT', 124
    tail = output[-4000:]
    # A limit message in a successful run may just be the model talking about limits; trust it only on failure,
    # except the explicit "usage limit" banner both CLIs print when they stop.
    limit_hit = bool(LIMIT_RE.search(tail)) and (code != 0 or 'usage limit' in tail.lower())
    log_usage({'ts': dt.datetime.now().isoformat(timespec='seconds'), 'engine': engine, 'role': role,
               'model': settings.get('model'), 'effort': settings.get('effort'), 'exit': code,
               'seconds': round(time.monotonic() - start), 'limit_hit': limit_hit})
    return {'engine': engine, 'role': role, 'code': LIMIT_EXIT if limit_hit else code, 'output': output, 'limit_hit': limit_hit}


def run(role, prompt, chrome=False, timeout=None, runner=subprocess.run):
    """Run a role on its engine; in dual mode fail over to the other engine when the first hits its limit."""
    cfg = load()
    engine = engine_for(role, cfg)
    result = run_once(engine, role, prompt, cfg, chrome, timeout, runner)
    if result['limit_hit'] and cfg['mode'] == 'dual' and cfg.get('failover', True):
        other = 'codex' if engine == 'claude' else 'claude'
        if binary(other):
            result = run_once(other, role, prompt, cfg, chrome, timeout, runner)
            result['failover_from'] = engine
    return result


def prompt_file(name, **values):
    text = (paths.ROOT / 'prompts' / name).read_text(encoding='utf-8')
    for key, value in values.items():
        text = text.replace('{{' + key + '}}', str(value))
    return text
