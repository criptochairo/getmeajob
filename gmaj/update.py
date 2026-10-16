"""Self-update of the engine (git pull --ff-only), safe to run at the start of every session and scheduled run.

Never breaks a session: offline, no git, local edits to engine files or a diverged branch -> skip with one line.
user/ is gitignored, so the user's data never blocks or is touched by the pull.
"""
import subprocess

from . import paths, tools

TIMEOUT = 30


def git(*args, runner=subprocess.run):
    return runner(['git', *args], cwd=paths.ROOT, capture_output=True, text=True, timeout=TIMEOUT)


def auto(runner=subprocess.run):
    """Returns {'status': updated|current|skipped, 'message': ...}."""
    try:
        if git('rev-parse', '--is-inside-work-tree', runner=runner).returncode != 0:
            return {'status': 'skipped', 'message': 'no es un clon de git (instalación manual): actualiza a mano'}
        if (git('status', '--porcelain', '--untracked-files=no', runner=runner).stdout or '').strip():
            return {'status': 'skipped', 'message': 'hay cambios locales en archivos del motor; no se actualizó (revisa `git status`)'}
        before = (git('rev-parse', 'HEAD', runner=runner).stdout or '').strip()
        pull = git('pull', '--ff-only', '--quiet', runner=runner)
        if pull.returncode != 0:
            return {'status': 'skipped', 'message': 'no se pudo actualizar (sin red o rama divergente): ' + (pull.stderr or '').strip()[:200]}
        after = (git('rev-parse', 'HEAD', runner=runner).stdout or '').strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status': 'skipped', 'message': f'no se pudo actualizar: {exc}'}
    if before == after:
        return {'status': 'current', 'message': 'GetMeAJob ya está al día'}
    changed = (git('diff', '--name-only', before, after, runner=runner).stdout or '').split()
    if any(f in ('uv.lock', 'pyproject.toml') for f in changed):
        runner(['uv', 'sync', '--quiet'], cwd=paths.ROOT, capture_output=True, text=True, timeout=300)
    tools.sync_skills()
    log = (git('log', '--format=- %s', f'{before}..{after}', runner=runner).stdout or '').strip()
    return {'status': 'updated', 'message': f'GetMeAJob actualizado ({before[:7]} → {after[:7]}):\n{log}'}
