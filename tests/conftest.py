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


@pytest.fixture
def approve_package(user_dir):
    def make(conn, ident):
        import json
        from gmaj import applications, approval, check_package, db
        folder = user_dir / applications.one(conn, ident)['dir']
        (folder / 'cv.md').write_text((user_dir / 'variants/cv_datos_es.md').read_text(encoding='utf-8'), encoding='utf-8')
        (folder / 'cover.md').write_text('Estimado equipo: me interesa la vacante de analista de datos para el equipo.', encoding='utf-8')
        (folder / 'answers.json').write_text('{"cv_language":"es"}', encoding='utf-8')
        (folder / 'cv.pdf').write_bytes(b'%PDF-1.4 fictional test')
        assert check_package.check(folder)['ok']
        snapshot = approval.content(folder)
        (folder / 'review.json').write_text(json.dumps({'verdict': 'approve', 'unsupported_claims': [], 'language_issues': []}), encoding='utf-8')
        approval.seal_review(folder, snapshot, 0)
        db.set_status(conn, ident, 'approved', agent='human')
        return folder
    return make
