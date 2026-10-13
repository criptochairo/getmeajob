"""Discovery without LLM: run the enabled fetchers into user/data/jobs.db and write fetch_report.json."""
import importlib
import json
from collections import Counter

from . import db, paths
from .fetchers.common import Client

SOURCES = ('remotive', 'remoteok', 'weworkremotely', 'himalayas', 'workingnomads',
           'linkedin_guest', 'computrabajo', 'greenhouse', 'lever', 'ashby', 'alignerr')


def enabled(config, source):
    options = (config.get('sources') or {}).get(source)
    if not options:
        return False
    return not isinstance(options, dict) or bool(options.get('enabled', False))


def fetch(conn, config, selected=None):
    report = {'ts': db.now(), 'sources': {}}
    paths.data().mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        if selected and source != selected:
            continue
        if not enabled(config, source):
            continue
        options = config['sources'][source]
        client = Client(source, options)
        # Fetchers can skip expensive detail requests for postings already stored.
        client.known = {r[0] for r in conn.execute('SELECT external_id FROM jobs WHERE source=? AND external_id IS NOT NULL', (source,))}
        # Último fetch de esta fuente: LinkedIn ajusta su ventana de fecha (f_TPR) a los días que no corrió.
        client.last_fetched = conn.execute('SELECT MAX(fetched_at) FROM jobs WHERE source=?', (source,)).fetchone()[0]
        counts = Counter(received=0, inserted=0, duplicates=0)
        try:
            module = importlib.import_module(f'{__package__}.fetchers.{source}')
            for item in module.fetch(config, client):
                counts['received'] += 1
                if not item.get('url') or not item.get('title'):
                    client.error('posting', 'Missing URL or title')
                    continue
                try:
                    counts['inserted' if db.insert_job(conn, item) else 'duplicates'] += 1
                except Exception as exc:
                    client.error(item.get('url'), exc)
        except Exception as exc:
            client.error('source', exc)
        finally:
            client.session.close()
        report['sources'][source] = {**counts, 'errors': client.errors}
        print(source + ': ' + json.dumps(dict(counts)) + f' errors={len(client.errors)}', flush=True)
        paths.data('fetch_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report
