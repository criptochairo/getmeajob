from .common import job, relevant

def compensation(pay):
    components = pay.get('summaryComponents') or [c for tier in pay.get('compensationTiers', []) for c in tier.get('components', [])]
    salaries = [c for c in components if c.get('compensationType') == 'Salary' and c.get('minValue') is not None]
    # Do not combine different currencies or payment intervals into one range.
    if salaries and len({(c.get('currencyCode'), c.get('interval')) for c in salaries}) == 1:
        return dict(low=min(c['minValue'] for c in salaries),
                    high=max(c.get('maxValue') or c['minValue'] for c in salaries),
                    currency=salaries[0].get('currencyCode'), period=salaries[0].get('interval'))
    return dict(text=pay.get('scrapeableCompensationSalarySummary') or pay.get('compensationTierSummary', ''))

def fetch(config, client):
    for slug in config['sources']['ashby']:
        try:
            data = client.get(f'https://api.ashbyhq.com/posting-api/job-board/{slug}', params={'includeCompensation': 'true'}).json()
            for item in data.get('jobs', []):
                if item.get('isListed', True) and relevant(item['title'], config):
                    desc = item.get('descriptionPlain') or item.get('descriptionHtml', '')
                    pay = item.get('compensation') or {}
                    yield job('ashby', item['title'], slug, item['jobUrl'], item['jobUrl'].rstrip('/').split('/')[-1],
                              item.get('location', ''), desc, remote=item.get('isRemote', False), mode=item.get('workplaceType'),
                              date=item.get('publishedAt'), **compensation(pay))
        except Exception as exc:
            client.board_error(slug, exc)
