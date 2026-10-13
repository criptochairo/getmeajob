from .common import job, relevant

def fetch(config, client):
    data = client.get(client.options['url']).json()
    for item in data:
        if relevant(item['title'], config):
            yield job('workingnomads', item['title'], item.get('company_name') or item.get('company', ''), item['url'], item.get('id'),
                      item.get('location', ''), item.get('description', ''), remote=True, date=item.get('pub_date'),
                      text=item.get('salary') or item.get('description', ''))
