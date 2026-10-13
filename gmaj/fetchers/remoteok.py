from .common import job, relevant

def fetch(config, client):
    for item in client.get(client.options['url']).json():
        if not item.get('position') or not relevant(item['position'], config, ' '.join(item.get('tags', []))):
            continue
        yield job('remoteok', item['position'], item.get('company', ''), item['url'], item.get('id'),
                  item.get('location', ''), item.get('description', ''), remote=True,
                  date=item.get('date'), low=item.get('salary_min') or None, high=item.get('salary_max') or None,
                  currency=item.get('salary_currency'), period='year', text=item.get('description', ''))
