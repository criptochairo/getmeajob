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
