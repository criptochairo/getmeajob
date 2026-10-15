import re

from conftest import ROOT
from gmaj import cli

WELCOME = (ROOT / 'docs' / 'welcome.txt').read_text(encoding='utf-8')


def test_welcome_fits_a_narrow_window():
    assert max(len(line) for line in WELCOME.splitlines()) <= 72


def test_welcome_steps_match_install_guide():
    """The welcome screen lists the same numbered steps as INSTALL.md (paso 0 is the welcome itself)."""
    install = (ROOT / 'INSTALL.md').read_text(encoding='utf-8')
    install_steps = [int(n) for n in re.findall(r'^## Paso (\d+)', install, re.M) if n != '0']
    welcome_steps = [int(n) for n in re.findall(r'^  (\d+)\. ', WELCOME, re.M)]
    assert welcome_steps == install_steps


def test_gmaj_without_command_shows_welcome(capsys):
    cli.main([])
    out = capsys.readouterr().out
    assert 'LOS PASOS' in out and 'uv run gmaj --help' in out


def test_cvs_message_groups_by_letter_with_absolute_links(user_dir):
    (user_dir / 'variants' / 'cv_datos_es.pdf').write_bytes(b'%PDF-1.4')
    message = cli.cvs_message()
    assert message.startswith('**A · ')
    pdf = (user_dir / 'variants' / 'cv_datos_es.pdf').resolve().as_posix()
    assert f'- CV en español: [cv_datos_es.pdf](<{pdf}>)' in message
