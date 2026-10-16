"""Export filtered jobs as compact batches for LLM scoring, and import the scores back.

  export -> user/data/score_batches/batch_NN.json; the scorer writes batch_NN.scores.json [{"id","score","reason"}]
  import -> reads every *.scores.json, sets status 'scored', archives the batch in done/
"""
import json
import shutil

from . import db, paths

HARD_REQ_CAP = 40   # score máximo cuando el scorer marca hard_req_mismatch


def batch_dir():
    return paths.data('score_batches')


def export(conn, batch_size=60, desc_chars=600):
    out = batch_dir()
    out.mkdir(parents=True, exist_ok=True)
    rows = conn.execute("SELECT * FROM jobs WHERE status='filtered' ORDER BY fetched_at").fetchall()
    jobs = [{
        'id': r['id'], 'title': r['title'], 'company': r['company'], 'location': r['location'],
        'work_mode': r['work_mode'], 'salary': [r['salary_min'], r['salary_max'], r['salary_currency'], r['salary_period']],
        'language': r['language'], 'description': ' '.join((r['description'] or '').split())[:desc_chars],
    } for r in rows]
    files = []
    for n in range(0, len(jobs), batch_size):
        path = out / f'batch_{n // batch_size:02d}.json'
        path.write_text(json.dumps(jobs[n:n + batch_size], ensure_ascii=False, indent=0), encoding='utf-8')
        files.append(path)
    return files


def import_scores(conn):
    done = batch_dir() / 'done'
    done.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in sorted(batch_dir().glob('*.scores.json')):
        for item in json.loads(path.read_text(encoding='utf-8-sig')):
            row = conn.execute('SELECT status FROM jobs WHERE id=?', (item['id'],)).fetchone()
            if not row or row['status'] != 'filtered':
                continue  # discarded since export by a newer prefilter rule
            score = max(0, min(100, int(item['score'])))
            if item.get('hard_req_mismatch') is True:
                score = min(score, HARD_REQ_CAP)   # requisito duro que el candidato no cumple (prompts/score.md)
            db.set_status(conn, item['id'], 'scored', item.get('reason', ''), score=score, score_reason=item.get('reason', ''))
            total += 1
        for f in (path, path.with_name(path.name.replace('.scores', ''))):
            if f.exists():
                shutil.move(str(f), done / f.name)
    conn.commit()
    return total
