from .common import job, relevant

def fetch(config, client):
    # The publisher recommends at most four downloads per day: fetch once,
    # then use the configured queries and relevance keywords locally.
    data = client.get(client.options['url']).json()
    for item in data.get('jobs', []):
        if not relevant(item['title'], config, ' '.join(item.get('tags', []))):
            continue
        yield job('remotive', item['title'], item['company_name'], item['url'], item['id'],
                  item.get('candidate_required_location', ''), item.get('description', ''),
                  remote=True, date=item.get('publication_date'), text=item.get('salary') or item.get('description', ''))
