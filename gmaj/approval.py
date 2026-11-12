"""Content bindings for checks, independent reviews, and approval before submission."""
import hashlib
import json
from pathlib import Path

from . import paths


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content(folder, require_pdf=True):
    folder = Path(folder)
    required = ('job.md', 'cv.md', 'cover.md', 'answers.json')
    if any(not (folder / name).is_file() for name in required) or (require_pdf and not list(folder.glob('*.pdf'))):
        raise ValueError('Paquete incompleto: faltan documentos o PDF; repite check + review + aprobación.')
    files = [folder / name for name in required] + sorted(folder.glob('*.pdf'))
    return {p.name: digest(p) for p in files}


def read(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value, dict):
            raise ValueError('Expected object')
        return value
    except (OSError, ValueError):
        raise ValueError('Falta una revisión vigente; repite check + review + aprobación.') from None


# This binding detects accidental or post-review edits, not a malicious agent:
# an agent with write access can forge it or claim --agent human. See docs/approval.md.
def seal_review(folder, snapshot, started_ns):
    """Called by the fresh-review wrapper, never by the tailoring process."""
    review = folder / 'review.json'
    if content(folder) != snapshot or review.stat().st_mtime_ns < started_ns:
        raise ValueError('El paquete cambió durante la revisión o no se generó una revisión nueva.')
    binding = {'content': snapshot, 'review': digest(review), 'check': digest(folder / 'check.json')}
    (folder / '.review-binding.json').write_text(json.dumps(binding, sort_keys=True), encoding='utf-8')


def validated(folder):
    snapshot = content(folder)
    check = read(folder / 'check.json')
    review = read(folder / 'review.json')
    binding = read(folder / '.review-binding.json')
    if (check.get('ok') is not True or check.get('content') != snapshot
            or review.get('verdict') != 'approve' or review.get('unsupported_claims')
            or review.get('language_issues') or review.get('reject_reason')
            or binding != {'content': snapshot, 'review': digest(folder / 'review.json'),
                           'check': digest(folder / 'check.json')}):
        raise ValueError('El contenido no tiene check y revisión válidos; repite check + review + aprobación.')
    return json.dumps(binding, sort_keys=True)


def before_send(conn, ident):
    from . import db
    row = conn.execute('SELECT * FROM jobs WHERE id=?', (ident,)).fetchone()
    if not row or row['status'] not in ('approved', 'needs_user'):
        raise ValueError('La vacante requiere check + review + aprobación antes de enviar.')
    try:
        if not row['approval_hash'] or not row['app_dir']:
            raise ValueError('Aprobación anterior sin huella: requiere check + review + re-aprobación.')
        if validated(paths.user(row['app_dir'])) != row['approval_hash']:
            raise ValueError('El paquete cambió tras aprobarlo: requiere check + review + re-aprobación.')
    except (ValueError, OSError) as exc:
        status = 'tailored'
        try:
            validated(paths.user(row['app_dir']))
            status = 'reviewed'
        except (ValueError, OSError, TypeError):
            pass
        db.set_status(conn, ident, status, note='approval invalidated: repeat check + review + approval')
        raise ValueError(str(exc)) from None
    return {'ok': True, 'id': ident}
