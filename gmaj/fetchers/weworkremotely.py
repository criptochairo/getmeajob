import feedparser
from .common import job, relevant

def fetch(config, client):
    feed = feedparser.parse(client.get(client.options['url']).content)
    if feed.bozo and not feed.entries:
        raise ValueError(f'Invalid RSS: {feed.bozo_exception}')
    for item in feed.entries:
        company, sep, title = item.title.partition(': ')
        if not sep:
            title, company = item.title, ''
        description = item.get('summary', '')
        if relevant(title, config):
            yield job('weworkremotely', title, company, item.link, item.get('id'),
                      description=description, remote=True, date=item.get('published'), text=description)
