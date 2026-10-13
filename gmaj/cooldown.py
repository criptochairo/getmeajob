"""Shared cool-down after a source blocks us (LinkedIn 429/403): every caller (daily fetch, sample) respects it.

State: user/data/<source>_cooldown.json = {"until": iso, "since": iso, "reason": "..."}.
"""
import datetime as dt
import json

from . import paths

DEFAULT_HOURS = 6


def _path(source):
    return paths.data(f'{source}_cooldown.json')


def _now():
    return dt.datetime.now(dt.timezone.utc)


def active(source, now=None):
    """Return the cool-down dict if still running, else None (and clean up an expired file)."""
    path = _path(source)
    try:
        state = json.loads(path.read_text(encoding='utf-8'))
        until = dt.datetime.fromisoformat(state['until'])
    except (FileNotFoundError, ValueError, KeyError):
        return None
    if (now or _now()) < until:
        return state
    path.unlink(missing_ok=True)
    return None


def start(source, reason, hours=DEFAULT_HOURS, now=None):
    now = now or _now()
    state = {'since': now.isoformat(), 'until': (now + dt.timedelta(hours=hours)).isoformat(), 'reason': str(reason)[:200]}
    path = _path(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
    return state


def describe(state):
    until = dt.datetime.fromisoformat(state['until']).astimezone()
    return f"en pausa hasta las {until:%H:%M} ({state['reason']})"
