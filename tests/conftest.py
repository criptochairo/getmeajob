import copy
import getpass
import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_USER = ROOT / 'tests' / 'fixtures' / 'user'
_CONFIG = yaml.safe_load((FIXTURE_USER / 'search.yaml').read_text(encoding='utf-8'))


def load_config():
    """Search config of the fictional test persona (never the real user's)."""
    return copy.deepcopy(_CONFIG)


@pytest.fixture(autouse=True)
def user_dir(tmp_path, monkeypatch):
    """Every test gets its own copy of the fictional user/ folder."""
    target = tmp_path / 'user'
    shutil.copytree(FIXTURE_USER, target)
    monkeypatch.setenv('GMAJ_USER_DIR', str(target))
    return target


def pytest_configure(config):
    # Per-user temp dir: Codex's sandbox user and the human's user can't delete each other's files.
    if not config.option.basetemp:
        base = ROOT / '.pytest-tmp'
        base.mkdir(exist_ok=True)
        config.option.basetemp = str(base / getpass.getuser())
