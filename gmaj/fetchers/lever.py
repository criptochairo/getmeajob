from .common import job, relevant

def fetch(config, client):
    for slug in client.live_slugs(config['sources']['lever']):
        try:
            data = client.get(f'https://api.lever.co/v0/postings/{slug}', params={'mode': 'json'}).json()
            for item in data:
                if relevant(item['text'], config):
                    desc = item.get('descriptionPlain', '') + ' ' + ' '.join(v.get('content', '') for v in item.get('lists', [])) + ' ' + item.get('additionalPlain', '')
                    pay = item.get('salaryRange') or {}
                    yield job('lever', item['text'], slug, item['hostedUrl'], f"{slug}:{item['id']}",
                              item.get('categories', {}).get('location', ''), desc,
                              mode=item.get('workplaceType'), date=item.get('createdAt', 0) / 1000 or None,
                              text=desc, low=pay.get('min'), high=pay.get('max'), currency=pay.get('currency'), period=pay.get('interval'))
        except Exception as exc:
            client.board_error(slug, exc)
