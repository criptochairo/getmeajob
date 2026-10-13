"""Check that user/ is complete enough for the daily run. No third-party schema library: a list of required paths."""
import re

import yaml

from . import paths

SCHEMA_VERSION = 1

REQUIRED = {
    'profile': ['personal.full_name', 'personal.email', 'personal.phone', 'personal.location.city', 'personal.location.country',
                'experience', 'education', 'languages', 'skills', 'cv_policy.pdf_name', 'preferences.roles_wanted'],
    'answers': ['work_authorization.countries_authorized', 'availability.notice_period', 'salary_expectation.currency',
                'salary_expectation.monthly', 'eeo_voluntary', 'escalate_always'],
    'search': ['market.country', 'currency.base', 'salary.floor_month', 'work_mode.remote', 'work_mode.hybrid', 'work_mode.onsite',
               'queries', 'relevance_keywords', 'sources', 'scoring.threshold_tailor', 'limits.per_platform_per_day',
               'variants', 'operation.autonomy'],
    'engines': ['mode'],
}
TODO = re.compile(r'\bTODO\b')


def lookup(tree, dotted):
    node = tree
    for key in dotted.split('.'):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def empty(value):
    return value is None or value == '' or value == [] or value == {}


def todo_paths(node, prefix=''):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from todo_paths(v, f'{prefix}.{k}' if prefix else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from todo_paths(v, f'{prefix}[{i}]')
    elif isinstance(node, str) and TODO.search(node):
        yield prefix


def check(user_dir=None):
    base = user_dir or paths.user_dir()
    problems, warnings, loaded = [], [], {}
    for name, required in REQUIRED.items():
        path = base / f'{name}.yaml'
        if not path.exists():
            problems.append(f'{name}.yaml no existe')
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        except yaml.YAMLError as exc:
            problems.append(f'{name}.yaml no es YAML válido: {exc}')
            continue
        loaded[name] = data
        if data.get('schema_version') != SCHEMA_VERSION:
            warnings.append(f'{name}.yaml: schema_version {data.get("schema_version")!r} (esperado {SCHEMA_VERSION}); corre `gmaj update`')
        problems += [f'{name}.yaml: falta {p}' for p in required if empty(lookup(data, p))]
        warnings += [f'{name}.yaml: {p} sigue en TODO (no se usará)' for p in todo_paths(data)]
    search = loaded.get('search') or {}
    for variant in search.get('variants') or []:
        for key in ('cv', 'cover'):
            if variant.get(key) and not (base / 'variants' / f"{variant[key]}.md").exists():
                problems.append(f"variants/{variant[key]}.md no existe (search.yaml variants)")
    langs = {v.get('language') for v in search.get('variants') or []}
    for lang in search.get('languages_allowed') or []:
        if lang not in langs:
            warnings.append(f'No hay variante de CV en "{lang}": se traducirá la más cercana en cada vacante')
    engines = loaded.get('engines') or {}
    if engines.get('mode') not in (None, 'claude', 'codex', 'dual'):
        problems.append('engines.yaml: mode debe ser claude, codex o dual')
    return {'ok': not problems, 'problems': problems, 'warnings': warnings}
