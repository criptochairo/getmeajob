from .common import job, queries, relevant

def fetch(config, client):
    for query in queries(config):
        for page in range(1, int(client.options.get('max_pages_per_query', 2)) + 1):
            try:
                data = client.get(client.options['url'], params={'q': query, 'page': page}).json()
                items = data.get('jobs', [])
                for item in items:
                    if not relevant(item['title'], config):
                        continue
                    location = ', '.join(str(v) for v in item.get('locationRestrictions', [])) or 'Worldwide'
                    yield job('himalayas', item['title'], item.get('companyName', ''), item.get('applicationLink') or item['guid'],
                              item.get('id') or item.get('guid'), location, item.get('description', ''), remote=True,
                              date=item.get('pubDate'), low=item.get('minSalary'), high=item.get('maxSalary'),
                              currency=item.get('currency'), period=item.get('salaryPeriod'), text=item.get('description', ''))
                if not items or len(items) < data.get('limit', 20) or page >= data.get('totalPages', (data.get('totalCount', 20) + 19) // 20):
                    break
            except Exception as exc:
                client.error(f'{query} page {page}', exc)
                break
