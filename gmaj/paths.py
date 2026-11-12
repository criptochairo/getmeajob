"""Where things live. The engine (this repo) is versioned; everything personal lives in user/ (gitignored).

GMAJ_USER_DIR overrides the user folder (tests, or several people on one PC).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def user_dir():
    return Path(os.environ.get('GMAJ_USER_DIR') or ROOT / 'user').resolve()


def user(*parts):
    return user_dir().joinpath(*parts)


def data(*parts):
    return user('data', *parts)


def applications(*parts):
    return user('applications', *parts)


def active():
    return {name: str(user(name).resolve()) for name in
            ('profile.yaml', 'answers.yaml', 'search.yaml', 'engines.yaml',
             'generated/candidate_brief.md', 'variants', 'applications', 'data', 'inbox', 'reports', 'state', 'logs')} | {'user_dir': str(user_dir())}
