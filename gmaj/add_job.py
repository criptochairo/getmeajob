"""Insert jobs found in the browser (OCC, Indeed, LinkedIn logged-in search) or in e-mail alerts into the DB as 'new'.

Input: a JSON list [{"source", "title", "company", "url" (optional when the source has offer_url), "external_id",
"location", "mode", "description", "date", "force" (skip the relevance filter for leads the user sent explicitly)}].
Run `gmaj prefilter` afterwards.
"""
import json

from . import db
from .fetchers.common import job, relevant

# Sources that only enter through the browser or mail; fetcher sources are accepted too.
EXTRA_SOURCES = ('occ', 'indeed', 'indeed_mx', 'linkedin_guest', 'mail', 'computrabajo', 'greenhouse', 'lever', 'ashby')


def load(path):
    # utf-8-sig: PowerShell 5.1 antepone BOM al canalizar JSON.
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def insert(conn, items, config):
    sources = config.get('sources') or {}
    counts = {'received': len(items), 'irrelevant': 0, 'inserted': 0}
    for item in items:
        source = item.get('source')
        if not source or (source not in sources and source not in EXTRA_SOURCES):
            raise ValueError(f'Unknown source {source!r}; add it to search.yaml sources')
        if not item.get('force') and not relevant(item['title'], config):
            counts['irrelevant'] += 1
            continue
        options = sources.get(source) if isinstance(sources.get(source), dict) else {}
        location = item.get('location', '')
        suffix = options.get('location_suffix')   # e.g. OCC lists only states: append the country so prefilter can place it
        if suffix and db.normalize(suffix) not in db.normalize(location):
            location = (location + ', ' + suffix).strip(', ')
        url = item.get('url') or (options.get('offer_url', '').format(id=item.get('external_id')) if options.get('offer_url') else None)
        if not url:
            raise ValueError(f"{source}: item without url: {item.get('title')}")
        record = job(source, item['title'], item.get('company', ''), url, external_id=item.get('external_id'),
                     location=location, description=item.get('description', ''),
                     remote=item.get('mode') == 'remote', mode=item.get('mode'), date=item.get('date'),
                     text=item.get('description', ''))
        counts['inserted'] += db.insert_job(conn, record)
    return counts
