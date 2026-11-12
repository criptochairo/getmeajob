"""Self-update of the engine (git pull --ff-only), safe to run at the start of every session and scheduled run.

Never breaks a session: offline, no git, local edits to engine files or a diverged branch -> skip with one line.
user/ is gitignored, so the user's data never blocks or is touched by the pull.
"""
import subprocess

from . import config, paths, tools

TIMEOUT = 15
SYNC_TIMEOUT = 90
MAX_SYNC_FAILURES = 3


def result(status, message):
    if status in ('updated', 'current'):
        try:
            notices = config.source_warnings(config.search())
        except Exception:
            # A missing or unreadable search config must not break self-update.
            notices = []
        if notices:
            message += '\n' + '\n'.join(notices)
    return {'status': status, 'message': message}


def git(*args, runner=subprocess.run):
    return runner(['git', *args], cwd=paths.ROOT, capture_output=True, text=True, timeout=TIMEOUT)


def auto(runner=subprocess.run):
    """Returns {'status': updated|current|skipped, 'message': ...}."""
    pending = paths.ROOT / '.gmaj-sync-pending'
    updated = False
    synced = False
    sync_error = None

    def checked_git(*args):
        result = git(*args, runner=runner)
        result.check_returncode()
        return (result.stdout or '').strip()

    def sync(dependencies=True):
        nonlocal synced
        if synced:
            return
        synced = True
        try:
            failures = int(pending.read_text(encoding='utf-8').strip() or '0')
        except (FileNotFoundError, ValueError):
            failures = 0
        blocked = dependencies and failures >= MAX_SYNC_FAILURES
        try:
            if dependencies and not blocked:
                result = runner(['uv', 'sync', '--quiet'], cwd=paths.ROOT, capture_output=True,
                                text=True, timeout=SYNC_TIMEOUT)
                result.check_returncode()
            tools.sync_skills()
            if not blocked:
                pending.unlink(missing_ok=True)
        except Exception:
            pending.write_text(str(failures if blocked else failures + 1), encoding='utf-8')
            raise
        if blocked:
            raise RuntimeError('Corre `uv sync` a mano y luego `uv run gmaj update --sync-complete` si termina bien.')

    try:
        # Retry before checking local edits or the network: a failed skills copy may
        # itself have left tracked files modified. Keep the marker until both finish.
        if pending.exists():
            try:
                sync()
            except Exception as exc:
                sync_error = exc
        if git('rev-parse', '--is-inside-work-tree', runner=runner).returncode != 0:
            return {'status': 'skipped', 'message': 'no es un clon de git (instalación manual): actualiza a mano'}
        if checked_git('status', '--porcelain', '--untracked-files=no'):
            return {'status': 'skipped', 'message': 'hay cambios locales en archivos del motor; no se actualizó (revisa `git status`)'}
        before = checked_git('rev-parse', 'HEAD')
        try:
            pull = git('pull', '--ff-only', '--quiet', runner=runner)
        except (subprocess.TimeoutExpired, OSError) as exc:
            pull = subprocess.CompletedProcess(['git', 'pull'], 1, stderr=str(exc))
        after = checked_git('rev-parse', 'HEAD')
        updated = before != after
        if pull.returncode != 0 and not updated:
            return {'status': 'skipped', 'message': 'sin red o rama divergente: ' + (pull.stderr or '')[:200]}
        if not updated:
            if sync_error is not None:
                raise sync_error
            pending.unlink(missing_ok=True)
            return result('current', 'GetMeAJob ya está al día')
        if not pending.exists():
            pending.write_text('0', encoding='utf-8')
        changed = checked_git('diff', '--name-only', before, after).split()
        sync(dependencies=any(f in ('uv.lock', 'pyproject.toml') for f in changed))
        if sync_error is not None:
            raise sync_error
        log = checked_git('log', '--format=- %s', f'{before}..{after}')
        return result('updated', f'GetMeAJob actualizado ({before[:7]} → {after[:7]}):\n{log}')
    except Exception as exc:
        # Updating is best-effort; even unexpected filesystem/skills errors must
        # not abort the session. Do not clear the recovery marker on failure.
        message = 'GetMeAJob actualizado' if updated else 'no se pudo completar la actualización'
        if pending.exists() and pending.read_text(encoding='utf-8').strip() == str(MAX_SYNC_FAILURES):
            return result('updated' if updated else 'skipped',
                          message + '; corre `uv sync` a mano y luego `uv run gmaj update --sync-complete` si termina bien.')
        if pending.exists():
            message += '; sincronización pendiente (se reintentará en la próxima ejecución)'
        return result('updated' if updated else 'skipped', f'{message}: {exc}')
