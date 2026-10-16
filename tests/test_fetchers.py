"""Offline contract checks for APIs that can fail or change independently."""
import requests
from conftest import load_config
from gmaj.fetchers import greenhouse, linkedin_guest, himalayas
from gmaj.fetchers.common import Client

def test_local_filter_handles_plural_and_title_modality():
    from gmaj.fetchers.common import relevant, job, clean
    assert clean('&lt;p&gt;Legal &amp;amp; compliance&lt;/p&gt;') == 'Legal & compliance'
    assert relevant('Data Analysts', load_config())
    assert relevant('Analista de datos Sr', load_config())
    assert not relevant('International Account Manager', load_config())
    assert job('test', 'Legal Analyst (Remote)', 'Acme', 'https://example.com')['work_mode'] == 'remote'

def test_computrabajo_actual_card_and_jsonld():
    import json
    from gmaj.fetchers.computrabajo import parse_cards, parse_detail
    html = '<article class="box_offer" data-id="abc"><h2><a href="/job">Data Analyst</a></h2><p class="dFlex fs16 fc_base"><span>4.5</span><a class="fc_base t_ellipsis">Acme</a></p><p class="fs16 fc_base"><span class="mr10">Mexico City</span></p><div class="fs13 mt15">Presencial y remoto</div></article>'
    card = list(parse_cards(html, 'https://example.com'))[0]
    assert card['company'] == 'Acme'
    assert card['location'] == 'Mexico City'
    assert card['mode'] == 'hybrid'
    posting = {'@type': 'JobPosting', 'description': 'Full description', 'salaryCurrency': 'MXN'}
    html = '<div class="box_detail">Wrong heading</div><script type="application/ld+json">' + json.dumps({'@graph': [posting]}) + '</script>'
    assert parse_detail(html) == posting

def test_computrabajo_zero_salary_is_unpublished(monkeypatch):
    import json
    from gmaj.fetchers import computrabajo
    client = Client('computrabajo', {'url': 'https://example.com', 'modality': 'remoto'})
    card = '<article class="box_offer" data-id="1"><h2><a href="/job">Data Analyst</a></h2></article>'
    posting = {'@type': 'JobPosting', 'description': 'Remote legal work', 'baseSalary': {'currency': 'MXN', 'value': {'value': 0, 'unitText': 'MONTH'}}}
    detail = '<script type="application/ld+json">' + json.dumps(posting) + '</script>'
    monkeypatch.setattr(client, 'get', lambda url: Response(text=detail if url.endswith('/job') else card))
    config = load_config()
    config['queries'] = {'en': ['data']}
    jobs = list(computrabajo.fetch(config, client))
    assert len(jobs) == 1
    assert jobs[0]['salary_min'] is None

def test_ashby_uses_structured_salary_and_ignores_equity():
    from gmaj.fetchers.ashby import compensation
    from gmaj.fetchers.common import salary
    pay = {'summaryComponents': [
        {'compensationType': 'EquityPercentage', 'minValue': 1},
        {'compensationType': 'Salary', 'minValue': 60000, 'maxValue': 80000, 'currencyCode': 'USD', 'interval': '1 YEAR'}]}
    result = salary(**compensation(pay))
    assert result == dict(salary_min=60000, salary_max=80000, salary_currency='USD', salary_period='year')

class Response:
    def __init__(self, data=None, text=''):
        self.data, self.text = data, text
    def json(self):
        return self.data

def test_invalid_board_does_not_stop_next(user_dir, monkeypatch):
    config = load_config()
    client = Client('greenhouse')
    def get(url, **kwargs):
        if '/bad/' in url:
            response = requests.Response()
            response.status_code = 404
            raise requests.HTTPError('404', response=response)
        return Response({'jobs': [{'id': 1, 'title': 'Data Analyst', 'absolute_url': 'https://example.com/1', 'location': {'name': 'Remote'}, 'content': 'Legal operations'}]})
    monkeypatch.setattr(client, 'get', get)
    config['sources']['greenhouse'] = ['bad', 'good']
    assert len(list(greenhouse.fetch(config, client))) == 1
    assert (user_dir / 'data/invalid_boards.txt').read_text().strip() == 'greenhouse/bad'
    assert len(client.errors) == 1

def test_linkedin_only_fetches_relevant_details(monkeypatch):
    def card(ident, title):
        return f'<div class="base-card" data-entity-urn="urn:li:jobPosting:{ident}"><h3 class="base-search-card__title">{title}</h3><a class="base-card__full-link" href="https://example.com/{ident}"></a></div>'
    client = Client('linkedin_guest', {'url': 'https://search.example', 'max_pages_per_query': 2, 'locations': ['Mexico']})
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        if 'jobPosting/' in url:
            return Response(text='<div class="show-more-less-html__markup">Remote LATAM legal work. USD 60,000 - 80,000 annually</div>')
        if kwargs['params']['start'] == 0:
            return Response(text=card('1', 'Data Analyst') + card('2', 'Accountant'))
        return Response(text='')
    monkeypatch.setattr(client, 'get', get)
    config = load_config()
    config['queries'] = {'en': ['data']}
    jobs = list(linkedin_guest.fetch(config, client))
    assert len(jobs) == 1
    assert jobs[0]['salary_min'] == 60000
    assert jobs[0]['salary_period'] == 'year'
    assert sum('jobPosting/' in u for u, _ in calls) == 1
    assert [k['params']['start'] for u, k in calls if u == client.options['url']] == [0]

def test_himalayas_page_limit_and_local_filter(monkeypatch):
    client = Client('himalayas', {'url': 'https://example.com', 'max_pages_per_query': 2})
    pages = []
    def get(url, params):
        pages.append(params['page'])
        items = [{'title': 'Data Analyst', 'companyName': 'Acme', 'guid': 'https://example.com/1', 'locationRestrictions': ['Mexico']}]
        items += [{'title': 'Accountant'}] * 19
        return Response({'jobs': items, 'limit': 20, 'totalCount': 100})
    monkeypatch.setattr(client, 'get', get)
    config = load_config()
    config['queries'] = {'en': ['data']}
    jobs = list(himalayas.fetch(config, client))
    assert pages == [1, 2]
    assert len(jobs) == 2


def test_adaptive_throttle_doubles_on_429_and_decays():
    client = Client('linkedin_guest', {'adaptive_step_seconds': 30, 'adaptive_max_seconds': 120, 'adaptive_decay': 0.5})
    for expected in (30, 60, 120, 120):
        client.throttle(True)
        assert client.slowdown == expected
    client.throttle(False)
    assert client.slowdown == 60
    plain = Client('himalayas')
    plain.throttle(True)
    assert plain.slowdown == 0


def test_invalid_board_is_skipped_next_run(user_dir, monkeypatch):
    config = load_config()
    (user_dir / 'data').mkdir(exist_ok=True)
    (user_dir / 'data/invalid_boards.txt').write_text('greenhouse/bad\n', encoding='utf-8')
    client = Client('greenhouse')
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return Response({'jobs': []})
    monkeypatch.setattr(client, 'get', get)
    config['sources']['greenhouse'] = ['bad', 'good']
    list(greenhouse.fetch(config, client))
    assert len(calls) == 1 and '/good/' in calls[0]
