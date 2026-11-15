"""Load the user's YAML files (user/*.yaml). Friendly error when onboarding has not produced them yet."""
import yaml

from . import paths

FILES = ('profile', 'answers', 'search', 'engines')


class MissingUserFile(RuntimeError):
    pass


def load(name):
    path = paths.user(f'{name}.yaml')
    if not path.exists():
        raise MissingUserFile(f'Falta {path}. Corre la entrevista (skill gmaj-onboarding) o `gmaj init`.')
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def search():
    return load('search')


def profile():
    return load('profile')


def answers():
    return load('answers')


def engines():
    return load('engines')


def get(tree, dotted, default=None):
    """get(cfg, 'salary.floor_month') -> value or default."""
    node = tree
    for key in dotted.split('.'):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def active_sources(cfg, browser=False):
    """Fuentes activas, aceptando el formato antiguo `fuente: true`.

    Búsqueda automática (`browser=False`): cuenta `enabled`.
    Navegador (`browser=True`): basta `browser: true`. En los portales que solo
    se barren por navegador (OCC, Indeed) `enabled` es `false` a propósito,
    porque la búsqueda automática no tiene recolector para ellos; no los apaga.
    """
    result = {}
    for name, value in (cfg.get('sources') or {}).items():
        options = {'enabled': value} if isinstance(value, bool) else value
        if not isinstance(options, dict):
            continue
        if browser:
            active = options.get('browser') is True
        else:
            active = options.get('enabled', options.get('browser', False)) is True
        if active:
            result[name] = options
    return result


def disabled_browser_sources(cfg):
    """Portales de navegador apagados a propósito con `browser: false`."""
    return {name: options for name, options in (cfg.get('sources') or {}).items()
            if isinstance(options, dict) and options.get('browser') is False}
