"""gmaj — GetMeAJob command line. Run `uv run gmaj --help` (or `python -m gmaj --help`)."""
import argparse
import datetime as dt
import json
import logging
import subprocess
import sys

from . import add_job, applications, check_package, config, db, doctor, engines, pace, paths, pipeline, prefilter
from . import render_cv, sample, schedule, score_io, scrub, tools, validate


def out(value):
    print(json.dumps(value, ensure_ascii=False, indent=1) if not isinstance(value, str) else value)


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return value


def connect():
    return db.connect()


def setup_logging():
    paths.data().mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.FileHandler(paths.data('fetch.log'), encoding='utf-8'), logging.StreamHandler()])


def folders(items):
    return [applications.resolve(f) for f in items]


def rel(folder):
    """Path as the engine (running in the repo root) should see it; absolute when user/ lives elsewhere."""
    try:
        return folder.resolve().relative_to(paths.ROOT).as_posix()
    except ValueError:
        return folder.resolve().as_posix()


# ---------- commands ----------

def cmd_discover(a):
    """Fetch + prefilter without LLM. This is what the OS scheduler runs every morning."""
    setup_logging()
    cfg = config.search()
    conn = connect()
    try:
        report = pipeline.fetch(conn, cfg)
        counts = prefilter.run(conn, cfg)
    finally:
        conn.close()
    stamp = {'date': dt.date.today().isoformat(), 'finished': db.now(), 'prefilter': counts,
             'sources': {k: {x: v[x] for x in ('received', 'inserted')} | {'errors': len(v['errors'])} for k, v in report['sources'].items()}}
    paths.data('discover_done.json').write_text(json.dumps(stamp, ensure_ascii=False, indent=1), encoding='utf-8')
    out(stamp)


def cmd_fetch(a):
    setup_logging()
    conn = connect()
    try:
        pipeline.fetch(conn, config.search(), a.source)
    finally:
        conn.close()


def cmd_prefilter(a):
    conn = connect()
    out(prefilter.run(conn, config.search()))


def cmd_list(a):
    conn = connect()
    fields = 'id,title,company,url,work_mode,salary_min,salary_max,salary_currency,salary_period,score,app_dir,description'
    rows = [dict(r) for r in conn.execute(f'SELECT {fields} FROM jobs WHERE status=? ORDER BY score DESC,fetched_at DESC,id LIMIT ?',
                                          (a.status, a.limit))]
    for row in rows:
        row['description'] = (row['description'] or '')[:4000]
    if a.json:
        out(rows)
    else:
        for row in rows:
            print(f"{row['id']} | {row['score']} | {row['title']} | {row['company']} | {row['work_mode']} | {row['url']}")


def cmd_set_status(a):
    db.set_status(connect(), a.id, a.status, a.note, a.app_dir, a.agent)


def cmd_set_score(a):
    if not 0 <= a.score <= 100:
        raise ValueError('score must be between 0 and 100')
    db.set_status(connect(), a.id, 'scored', a.reason, score=a.score, score_reason=a.reason)


def cmd_stats(a):
    conn = connect()
    out({label: {row[0]: row[1] for row in conn.execute(f'SELECT {field},COUNT(*) FROM jobs GROUP BY {field}')}
         for label, field in [('by_status', 'status'), ('by_source', 'source')]})


def cmd_add_jobs(a):
    conn = connect()
    try:
        out(add_job.insert(conn, add_job.load(a.file), config.search()))
    finally:
        conn.close()


def cmd_score(a):
    conn = connect()
    if a.action == 'export':
        files = score_io.export(conn, a.batch_size, a.desc_chars)
        out([rel(f) for f in files])
    elif a.action == 'import':
        out(f'imported {score_io.import_scores(conn)} scores')
    else:  # run: export, score every batch with a fresh call of the scoring role, import
        files = score_io.export(conn, a.batch_size, a.desc_chars)
        results, limit_hit = [], False
        for f in files:
            prompt = engines.prompt_file('score.md', BATCH=rel(f), OUT=rel(f.with_name(f.stem + '.scores.json')))
            r = engines.run('score', prompt, timeout=1800)
            results.append({'batch': f.name, 'engine': r['engine'], 'code': r['code']})
            if r['limit_hit']:
                limit_hit = True
                break
        imported = score_io.import_scores(conn)   # keep what was scored even if a later batch failed
        failed = [x['batch'] for x in results if x['code'] != 0]
        out({'imported': imported, 'failed_batches': failed, 'limit_hit': limit_hit, 'results': results})
        if limit_hit:
            sys.exit(engines.LIMIT_EXIT)
        sys.exit(1 if failed else 0)


def cmd_top(a):
    out(applications.top(connect(), config.search(), a.min_score, a.limit))


def cmd_one(a):
    out(applications.one(connect(), a.id))


def batch_role(role, prompt_name, items, extra=''):
    dirs = folders(items)
    listing = '\n'.join('- ' + rel(d) for d in dirs)
    r = engines.run(role, engines.prompt_file(prompt_name, FOLDERS=listing, EXTRA=extra), timeout=3600)
    print(r['output'][-3000:])
    if r['limit_hit']:
        print('ENGINE_LIMIT')
        sys.exit(engines.LIMIT_EXIT)
    sys.exit(0 if r['code'] == 0 else 1)


def cmd_tailor(a):
    batch_role('tailor_high' if a.high else 'tailor', 'tailor.md', a.folders,
               'Adaptación COMPLETA (score alto).' if a.high else 'Adaptación según el score de cada job.md.')


def cmd_review(a):
    batch_role('review', 'review.md', a.folders)


def cmd_mail(a):
    r = engines.run('mail', engines.prompt_file('mail_triage.md', DATE=dt.date.today().isoformat()), timeout=1800)
    print(r['output'][-2000:])
    sys.exit(engines.LIMIT_EXIT if r['limit_hit'] else 0 if r['code'] == 0 else 1)


def cmd_check(a):
    rules = check_package.rules()
    bad = 0
    for folder in folders(a.folders):
        r = check_package.check(folder, *rules)
        bad += not r['ok']
        print(('OK   ' if r['ok'] else 'FAIL ') + rel(folder) + ('' if r['ok'] else ' -> ' + '; '.join(r['issues'])))
    sys.exit(1 if bad else 0)


def cmd_render(a):
    print(render_cv.render(a.src, a.out))


def cmd_pace(a):
    print(pace.pause(config.search().get('limits') or {}))


def cmd_cap(a):
    print(pace.status(config.search().get('limits') or {}, a.channel))


def cmd_log_applied(a):
    folder = applications.log_submission(connect(), a.folder, a.status, a.channel, a.note or '', a.agent)
    print('logged', rel(folder), a.status)


def cmd_engines(a):
    if a.action == 'set':
        path = paths.user('engines.yaml')
        text = path.read_text(encoding='utf-8') if path.exists() else (paths.ROOT / 'templates/user/engines.yaml').read_text(encoding='utf-8')
        import re
        text, n = re.subn(r'(?m)^mode:.*$', f'mode: {a.mode}', text)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text if n else f'mode: {a.mode}\n' + text, encoding='utf-8')
    cfg = engines.load()
    out({'mode': cfg['mode'],
         'cli': {e: engines.binary(e) for e in engines.ENGINES},
         'roles': {r: {'engine': engines.engine_for(r, cfg), **engines.role_settings(r, engines.engine_for(r, cfg), cfg)} for r in engines.ROLES}})


def cmd_run_role(a):
    prompt = open(a.prompt_file, encoding='utf-8').read() if a.prompt_file else sys.stdin.read()
    r = engines.run(a.role, prompt, chrome=a.chrome, timeout=a.timeout)
    print(r['output'][-4000:])
    sys.exit(engines.LIMIT_EXIT if r['limit_hit'] else r['code'])


def cmd_run_daily(a):
    """CLI/headless mode (advanced): discovery, then the orchestrator role with the gmaj-daily skill and the browser."""
    if not a.skip_discover:
        subprocess.run([sys.executable, '-m', 'gmaj', 'discover'], cwd=paths.ROOT)
    prompt = engines.prompt_file('daily.md', DATE=dt.date.today().isoformat())
    r = engines.run('orchestrate', prompt, chrome=True, timeout=6 * 3600)
    log = paths.user('logs', f'daily_{dt.date.today().isoformat()}.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(r['output'], encoding='utf-8')
    sys.exit(engines.LIMIT_EXIT if r['limit_hit'] else r['code'])


def cmd_schedule(a):
    if a.action == 'install':
        ok, msg = schedule.install(a.kind, a.time)
    elif a.action == 'remove':
        ok, msg = schedule.remove(a.kind)
    else:
        ok = schedule.status(a.kind)
        msg = 'registrada' if ok else 'no registrada'
    print(msg)
    sys.exit(0 if ok else 1)


def cmd_sample(a):
    out(sample.run(a.queries, a.location))


def cmd_collector(a):
    print(tools.collector(a.kind))


def cmd_sync_skills(a):
    diffs = tools.sync_skills(check_only=a.check)
    out(diffs or 'skills sincronizadas')
    sys.exit(1 if a.check and diffs else 0)


def cmd_scrub(a):
    findings = scrub.scan()
    for path, line, what in findings:
        print(f'{path}:{line}: {what}')
    print(f'{len(findings)} hallazgos')
    sys.exit(1 if findings else 0)


def cmd_validate(a):
    r = validate.check(only=a.only.split(',') if a.only else None)
    out(r)
    sys.exit(0 if r['ok'] else 1)


def cmd_doctor(a):
    sys.exit(doctor.main(a.json))


def cmd_init(a):
    out({'user_dir': str(paths.user_dir()), 'created': tools.init_user(git=not a.no_git)})


def cmd_autonomy(a):
    if a.action == 'record':
        out(tools.record_approval(clean=not a.corrected))
    elif a.action == 'set':
        out(tools.set_autonomy(a.mode))
    else:
        out(tools.autonomy_state())


def cmd_welcome(a):
    print((paths.ROOT / 'docs' / 'welcome.txt').read_text(encoding='utf-8'))


def cmd_update(a):
    r = subprocess.run(['git', 'pull', '--ff-only'], cwd=paths.ROOT)
    tools.sync_skills()
    v = validate.check()
    out({'git_pull': r.returncode, 'validate': v})


# ---------- parser ----------

def build():
    p = argparse.ArgumentParser(prog='gmaj', description='GetMeAJob 1.0 by Criptochairo')
    s = p.add_subparsers(dest='command')

    def add(name, func, help_text):
        sp = s.add_parser(name, help=help_text)
        sp.set_defaults(func=func)
        return sp

    add('welcome', cmd_welcome, 'pantalla de bienvenida: qué hace, pasos y tiempos')
    add('init', cmd_init, 'crea user/ desde las plantillas').add_argument('--no-git', action='store_true')
    add('doctor', cmd_doctor, 'revisa el entorno').add_argument('--json', action='store_true')
    add('validate', cmd_validate, 'revisa que el perfil esté completo').add_argument('--only', help='p. ej. profile,answers')
    add('update', cmd_update, 'actualiza el motor (git pull) y revisa el perfil')
    add('discover', cmd_discover, 'fetch + prefilter sin LLM (lo corre el programador del SO)')
    sp = add('fetch', cmd_fetch, 'solo descubrir vacantes')
    sp.add_argument('--source', choices=pipeline.SOURCES)
    add('prefilter', cmd_prefilter, 'filtros duros')
    sp = add('list', cmd_list, 'lista vacantes por estado')
    sp.add_argument('--status', choices=db.STATES, required=True)
    sp.add_argument('--limit', type=positive, default=50)
    sp.add_argument('--json', action='store_true')
    sp = add('set-status', cmd_set_status, 'cambia el estado de una vacante')
    sp.add_argument('id')
    sp.add_argument('status', choices=db.STATES)
    sp.add_argument('--note')
    sp.add_argument('--app-dir')
    sp.add_argument('--agent', choices=db.AGENTS)
    sp = add('set-score', cmd_set_score, 'asigna score manual')
    sp.add_argument('id')
    sp.add_argument('score', type=int)
    sp.add_argument('--reason', required=True)
    add('stats', cmd_stats, 'conteos por estado y fuente')
    add('add-jobs', cmd_add_jobs, 'inserta vacantes de un JSON (navegador / correo)').add_argument('file')
    sp = add('score', cmd_score, 'scoring en lotes: export | import | run')
    sp.add_argument('action', choices=['export', 'import', 'run'])
    sp.add_argument('--batch-size', type=positive, default=60)
    sp.add_argument('--desc-chars', type=positive, default=600)
    sp = add('top', cmd_top, 'crea carpetas de aplicación para las mejores vacantes (idempotente)')
    sp.add_argument('--min-score', type=int)
    sp.add_argument('--limit', type=positive, default=10)
    add('one', cmd_one, 'crea la carpeta de una vacante').add_argument('id')
    sp = add('tailor', cmd_tailor, 'adapta CV/carta/respuestas con el motor configurado')
    sp.add_argument('folders', nargs='+')
    sp.add_argument('--high', action='store_true', help='adaptación completa (score >= 75)')
    add('review', cmd_review, 'revisión cruzada con contexto limpio').add_argument('folders', nargs='+')
    add('mail', cmd_mail, 'triage de correo (solo lectura)')
    add('check', cmd_check, 'verificación sin IA de paquetes').add_argument('folders', nargs='+')
    sp = add('render', cmd_render, 'Markdown -> PDF')
    sp.add_argument('src')
    sp.add_argument('out', nargs='?')
    add('pace', cmd_pace, 'pausa humana entre envíos')
    add('cap', cmd_cap, 'tope de hoy para un canal y cuántos van').add_argument('channel')
    sp = add('log-applied', cmd_log_applied, 'registra un envío o escalamiento')
    sp.add_argument('folder')
    sp.add_argument('status', choices=db.STATES)
    sp.add_argument('channel')
    sp.add_argument('note', nargs='?')
    sp.add_argument('--agent', choices=db.AGENTS, default='claude')
    sp = add('engines', cmd_engines, 'muestra o cambia el modo de motores')
    sp.add_argument('action', choices=['show', 'set'], nargs='?', default='show')
    sp.add_argument('mode', nargs='?', choices=['claude', 'codex', 'dual'])
    sp = add('run-role', cmd_run_role, 'corre un rol con un prompt (avanzado)')
    sp.add_argument('role', choices=engines.ROLES)
    sp.add_argument('--prompt-file')
    sp.add_argument('--chrome', action='store_true')
    sp.add_argument('--timeout', type=positive)
    add('run-daily', cmd_run_daily, 'corrida completa por CLI (modo avanzado)').add_argument('--skip-discover', action='store_true')
    sp = add('schedule', cmd_schedule, 'programa la tarea diaria en el SO')
    sp.add_argument('action', choices=['install', 'remove', 'status'])
    sp.add_argument('--kind', choices=['discover', 'daily'], default='discover')
    sp.add_argument('--time', default='08:30')
    sp = add('sample', cmd_sample, 'cuenta vacantes recientes por consulta (sugerir roles)')
    sp.add_argument('queries', nargs='+')
    sp.add_argument('--location')
    add('collector', cmd_collector, 'genera el colector JS de OCC o Indeed').add_argument('kind', choices=['occ', 'indeed'])
    add('sync-skills', cmd_sync_skills, 'copia .agents/skills a .claude/skills').add_argument('--check', action='store_true')
    add('scrub', cmd_scrub, 'busca datos personales antes de publicar')
    sp = add('autonomy', cmd_autonomy, 'modo supervisado / piloto automático')
    sp.add_argument('action', choices=['show', 'record', 'set'], nargs='?', default='show')
    sp.add_argument('mode', nargs='?', choices=['supervised', 'autopilot'])
    sp.add_argument('--corrected', action='store_true', help='la aprobación necesitó correcciones')
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            pass
    parser = build()
    args = parser.parse_args(argv)
    if args.command is None:
        cmd_welcome(args)
        print('Comandos: uv run gmaj --help')
        return
    if args.command == 'engines' and args.action == 'set' and not args.mode:
        parser.error('engines set requiere un modo: claude | codex | dual')
    if args.command == 'autonomy' and args.action == 'set' and not args.mode:
        parser.error('autonomy set requiere: supervised | autopilot')
    try:
        args.func(args)
    except (ValueError, FileNotFoundError, config.MissingUserFile) as exc:
        parser.exit(2, f'gmaj: {exc}\n')


if __name__ == '__main__':
    main()
