"""LinkedIn rate limits: shared cool-down respected by the daily fetch and the market sample."""
import datetime as dt

import requests

from gmaj import cooldown, sample
from gmaj.fetchers import linkedin_guest
from gmaj.fetchers.common import Client


class Response:
    def __init__(self, text='', data=None):
        self.text, self.data = text, data

    def json(self):
        return self.data


def blocked_error():
    response = requests.Response()
    response.status_code = 429
    return requests.HTTPError('429', response=response)


def test_cooldown_expires(user_dir):
    now = dt.datetime(2026, 10, 13, 10, tzinfo=dt.timezone.utc)
    cooldown.start('linkedin_guest', 'test', hours=6, now=now)
    assert cooldown.active('linkedin_guest', now=now + dt.timedelta(hours=5))
    assert cooldown.active('linkedin_guest', now=now + dt.timedelta(hours=7)) is None
    assert not (user_dir / 'data/linkedin_guest_cooldown.json').exists()


def test_fetch_skips_linkedin_during_cooldown(monkeypatch):
    from conftest import load_config
    cooldown.start('linkedin_guest', 'bloqueo previo')
    client = Client('linkedin_guest', {'url': 'https://search.example'})
    monkeypatch.setattr(client, 'get', lambda *a, **k: (_ for _ in ()).throw(AssertionError('no debe llamar a LinkedIn')))
    assert list(linkedin_guest.fetch(load_config(), client)) == []
    assert 'en pausa' in client.errors[0]


def test_fetch_starts_cooldown_after_consecutive_blocks(monkeypatch):
    from conftest import load_config
    client = Client('linkedin_guest', {'url': 'https://search.example', 'pause_on_block_seconds': 0, 'max_consecutive_blocks': 2,
                                       'or_group_size': 1, 'cooldown_hours': 3})
    monkeypatch.setattr(client, 'get', lambda *a, **k: (_ for _ in ()).throw(blocked_error()))
    assert list(linkedin_guest.fetch(load_config(), client)) == []
    state = cooldown.active('linkedin_guest')
    assert state and 'bloqueos' in state['reason']


def fake_clients(li_get):
    li, other = Client('linkedin_guest', {}), Client('sample', {})
    li.get = li_get
    other.get = lambda url, **k: Response(data={'totalCount': 7, 'jobs': []}) if 'himalayas' in url else Response('')
    return li, other


def test_sample_caps_linkedin_queries():
    calls = []
    li, other = fake_clients(lambda url, params: calls.append(params['keywords']) or Response('<div class="base-card"></div>' * 10))
    result = sample.run([f'q{i}' for i in range(10)], location='Mexico', li_client=li, other_client=other)
    assert len(calls) == sample.MAX_LINKEDIN_QUERIES
    assert result['results'][0]['linkedin'] == '10+'
    assert result['results'][-1]['linkedin'].startswith('omitido')
    assert result['results'][-1]['himalayas_remote'] == '7'


def test_sample_stops_linkedin_on_block_and_shares_cooldown():
    calls = []

    def get(url, params):
        calls.append(params['keywords'])
        raise blocked_error()
    li, other = fake_clients(get)
    result = sample.run(['a', 'b', 'c'], location='Mexico', li_client=li, other_client=other)
    assert calls == ['a']
    assert all('en pausa' in r['linkedin'] for r in result['results'])
    assert cooldown.active('linkedin_guest')
