"""Human pacing with jitter (search.yaml limits): pause between submissions and today's effective cap per channel."""
import datetime as dt
import json
import random
import time

from . import paths


def cap(limits, channel, today=None):
    """per_platform_per_day reduced at random up to jitter_pct, fixed per date and channel.
    New accounts start lower: limits.first_week_per_day applies during the first 7 days after limits.start_date."""
    today = today or dt.date.today()
    jitter = limits.get('jitter_pct', 10) / 100
    caps = limits.get('per_platform_per_day') or {'default': 10}
    value = caps.get(channel, caps.get('default', 10))
    start = limits.get('start_date')
    if start and limits.get('first_week_per_day') and (today - dt.date.fromisoformat(str(start))).days < 7:
        value = min(value, limits['first_week_per_day'])
    rng = random.Random(today.isoformat() + channel)
    return max(1, round(value * (1 - rng.uniform(0, jitter))))


def sent_today(channel, today=None):
    """Count today's submissions for a channel from the applications' submission.log files."""
    stamp = (today or dt.date.today()).isoformat()
    total = 0
    for log in paths.applications().glob('*/submission.log'):
        text = log.read_text(encoding='utf-8', errors='ignore')
        for block in text.split('\nstatus: ')[1:]:
            if block.startswith('applied') and f'channel: {channel}' in block and f'time: {stamp}' in block:
                total += 1
    return total


def pause(limits, sleep=time.sleep):
    jitter = limits.get('jitter_pct', 10) / 100
    low, high = limits.get('pause_between_applications_seconds', [45, 120])
    seconds = random.uniform(low, high) * random.uniform(1 - jitter, 1 + jitter)
    sleep(seconds)
    return round(seconds)


def status(limits, channel):
    allowed = cap(limits, channel)
    used = sent_today(channel)
    return json.dumps({'channel': channel, 'cap_today': allowed, 'sent_today': used, 'remaining': max(0, allowed - used)})
