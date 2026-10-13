"""Where things live. The engine (this repo) is versioned; everything personal lives in user/ (gitignored).

GMAJ_USER_DIR overrides the user folder (tests, or several people on one PC).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def user_dir():
    return Path(os.environ.get('GMAJ_USER_DIR') or ROOT / 'user')


def user(*parts):
    return user_dir().joinpath(*parts)


def data(*parts):
    return user('data', *parts)


def applications(*parts):
    return user('applications', *parts)
