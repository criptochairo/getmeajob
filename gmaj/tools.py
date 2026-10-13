"""Small utilities: set up user/, render the in-browser collectors, mirror skills, supervised-mode state."""
import filecmp
import json
import re
import shutil
import subprocess

from . import config, db, paths

USER_DIRS = ('data', 'applications', 'inbox', 'reports', 'logs', 'documents', 'variants', 'onboarding', 'state', 'generated')


def init_user(git=True):
    """Create user/ from templates/user without overwriting anything the user already has."""
    base = paths.user_dir()
    created = []
    for name in USER_DIRS:
        (base / name).mkdir(parents=True, exist_ok=True)
    for src in (paths.ROOT / 'templates' / 'user').rglob('*'):
        if src.is_file():
            dst = base / src.relative_to(paths.ROOT / 'templates' / 'user')
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                created.append(dst.relative_to(base).as_posix())
    if git and shutil.which('git') and not (base / '.git').exists():
        # Local history of the user's own data (undo, diffs). No remote unless the user adds one.
        subprocess.run(['git', 'init', '-q', '-b', 'main'], cwd=base)
        (base / '.gitignore').write_text('data/score_batches/\nlogs/last_*\n*.tmp\n', encoding='utf-8')
    return created


# ---------- in-browser collectors (OCC / Indeed) ----------

def js(value):
    return json.dumps(value, ensure_ascii=False)


def relevance_regex(cfg):
    words = cfg.get('relevance_keywords') or []
    return '|'.join(re.escape(db.normalize(w)) for w in words if str(w).strip()) or '.'


def collector(kind):
    cfg = config.search()
    template = (paths.ROOT / 'prompts' / f'{kind}_collect.js').read_text(encoding='utf-8')
    queries = list(dict.fromkeys(q for values in (cfg.get('queries') or {}).values() for q in values))
    floor = (cfg.get('salary') or {}).get('floor_month') or 0
    source = (cfg.get('sources') or {}).get('occ' if kind == 'occ' else 'indeed') or {}
    values = {
        '__QUERIES__': js([re.sub(r'[^a-z0-9]+', '-', db.normalize(q)).strip('-') for q in queries] if kind == 'occ' else queries),
        '__FLOOR__': str(int(floor)),
        '__RELEVANT__': js(relevance_regex(cfg)),
        '__KEEP_ONSITE__': 'true' if (cfg.get('work_mode') or {}).get('onsite') != 'reject' else 'false',
        '__LOCATIONS__': js(source.get('locations') or [config.get(cfg, 'market.city') or config.get(cfg, 'market.country_label') or '']),
        '__HOME__': js('|'.join(re.escape(z) for z in (config.get(cfg, 'work_mode.zones.ok') or []) + [config.get(cfg, 'market.city') or ''] if z) or '$^'),
    }
    for token, value in values.items():
        template = template.replace(token, value)
    return template


# ---------- skills mirror: .agents/skills (canonical, Codex) -> .claude/skills (Claude) ----------

def sync_skills(check_only=False):
    src, dst = paths.ROOT / '.agents' / 'skills', paths.ROOT / '.claude' / 'skills'
    diffs = []
    for path in src.rglob('*'):
        if path.is_file():
            target = dst / path.relative_to(src)
            if not target.exists() or not filecmp.cmp(path, target, shallow=False):
                diffs.append(target.relative_to(paths.ROOT).as_posix())
                if not check_only:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
    for path in dst.rglob('*') if dst.exists() else []:
        if path.is_file() and not (src / path.relative_to(dst)).exists():
            diffs.append(path.relative_to(paths.ROOT).as_posix() + ' (sobra)')
            if not check_only:
                path.unlink()
    return diffs


# ---------- supervised -> autopilot ----------

def state_path():
    return paths.user('state', 'state.json')


def autonomy_state():
    try:
        state = json.loads(state_path().read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        cfg = config.search()
        state = {'autonomy': config.get(cfg, 'operation.autonomy', 'supervised'), 'clean_approvals': 0, 'corrected_approvals': 0}
    return state


def save_state(state):
    state_path().parent.mkdir(parents=True, exist_ok=True)
    state_path().write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
    return state


def record_approval(clean=True):
    state = autonomy_state()
    state['clean_approvals' if clean else 'corrected_approvals'] += 1
    threshold = config.get(config.search(), 'operation.supervised_until_clean_approvals', 10)
    state['offer_autopilot'] = state['autonomy'] == 'supervised' and state['clean_approvals'] >= threshold
    return save_state(state)


def set_autonomy(mode):
    if mode not in ('supervised', 'autopilot'):
        raise ValueError('autonomy: supervised | autopilot')
    state = autonomy_state()
    state['autonomy'] = mode
    state['offer_autopilot'] = False
    return save_state(state)
