from .common import job, relevant

def fetch(config, client):
    for slug in config['sources']['greenhouse']:
        try:
            data = client.get(f'https://boards-api.greenhouse.io/v1/boards/{slug}/jobs', params={'content': 'true'}).json()
            for item in data.get('jobs', []):
                if relevant(item['title'], config):
                    desc = item.get('content', '')
                    yield job('greenhouse', item['title'], slug, item['absolute_url'], f"{slug}:{item['id']}",
                              item.get('location', {}).get('name', ''), desc, date=item.get('updated_at'), text=desc)
        except Exception as exc:
            client.board_error(slug, exc)
