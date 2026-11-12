import json
import sqlite3
import time

import pytest

from gmaj import applications, approval, cli, db, engines


def record(conn):
    job = dict(source='test', external_id='1', url='https://example.com/1',
               title='Analista de datos', company='Example', description='SQL')
    db.insert_job(conn, job)
    return db.job_id(job)


@pytest.mark.parametrize('name', ['cv.md', 'cv.pdf', 'cover.md', 'answers.json', 'job.md',
                                 'review.json', 'check.json', 'extra.pdf'])
def test_changed_approval_blocks_send_and_invalidates(name, approve_package):
    conn = db.connect()
    ident = record(conn)
    folder = approve_package(conn, ident)
    assert approval.before_send(conn, ident)['ok']
    with (folder / name).open('ab') as stream:
        stream.write(b' changed')
    with pytest.raises(ValueError):
        approval.before_send(conn, ident)
    assert conn.execute('SELECT status,approval_hash FROM jobs').fetchone()[:] == ('tailored', None)
    with pytest.raises(ValueError):
        db.set_status(conn, ident, 'approved', agent='human')


def test_requires_independent_current_review_and_human_in_supervised(approve_package):
    conn = db.connect()
    ident = record(conn)
    with pytest.raises(ValueError):
        db.set_status(conn, ident, 'approved', agent='human')
    folder = approve_package(conn, ident)
    with pytest.raises(ValueError, match='human'):
        db.set_status(conn, ident, 'approved', agent='codex')
    (folder / '.review-binding.json').unlink()
    with pytest.raises(ValueError):
        db.set_status(conn, ident, 'approved', agent='human')


def test_review_wrapper_binds_only_fresh_unchanged_output(approve_package, monkeypatch):
    conn = db.connect()
    folder = approve_package(conn, record(conn))
    snapshot = approval.content(folder)
    with pytest.raises(ValueError):
        approval.seal_review(folder, snapshot, time.time_ns() + 10**9)

    def review(role, prompt, **kwargs):
        assert role == 'review'
        (folder / 'review.json').write_text('{"verdict":"approve"}', encoding='utf-8')
        return {'code': 0, 'output': '', 'limit_hit': False}

    monkeypatch.setattr(engines, 'run', review)
    with pytest.raises(SystemExit) as result:
        cli.main(['review', str(folder)])
    assert result.value.code == 0
    assert approval.validated(folder)
    (folder / 'cv.pdf').write_bytes(b'new PDF')
    with pytest.raises(ValueError):
        approval.seal_review(folder, snapshot, 0)


def test_existing_database_upgrade_and_legacy_approval(tmp_path, approve_package):
    file = tmp_path / 'legacy.db'
    conn = db.connect(file)
    ident = record(conn)
    approve_package(conn, ident)
    conn.execute('ALTER TABLE jobs DROP COLUMN approval_hash')
    conn.commit()
    conn.close()
    for _ in range(2):
        conn = db.connect(file)
        assert [r[1] for r in conn.execute('PRAGMA table_info(jobs)')].count('approval_hash') == 1
        conn.close()
    conn = db.connect(file)
    with pytest.raises(ValueError, match='huella'):
        approval.before_send(conn, ident)
    assert conn.execute('SELECT status FROM jobs').fetchone()[0] == 'reviewed'


def test_cli_before_send_and_resume(approve_package, capsys):
    conn = db.connect()
    ident = record(conn)
    db.set_status(conn, ident, 'scored', score=80)
    folder = applications.one(conn, ident)['dir']
    assert applications.resume(conn)[0]['next'] == 'tailor'
    folder = approve_package(conn, ident)
    assert applications.top(conn, {}) == []
    assert applications.resume(conn)[0]['next'] == 'send'
    cli.main(['before-send', str(folder)])
    assert json.loads(capsys.readouterr().out)['ok']
    (folder / 'cv.pdf').unlink()
    with pytest.raises(SystemExit) as result:
        cli.main(['before-send', str(folder)])
    assert result.value.code == 2
    assert conn.execute('SELECT status FROM jobs').fetchone()[0] == 'tailored'


def test_rejected_review_cannot_be_approved(approve_package):
    conn = db.connect()
    ident = record(conn)
    folder = approve_package(conn, ident)
    (folder / 'review.json').write_text('{"verdict":"reject"}', encoding='utf-8')
    approval.seal_review(folder, approval.content(folder), 0)
    with pytest.raises(ValueError):
        db.set_status(conn, ident, 'approved', agent='human')


@pytest.mark.parametrize('via_log', [False, True])
def test_confirmed_submission_is_recorded_even_if_content_changed(approve_package, via_log):
    conn = db.connect()
    ident = record(conn)
    folder = approve_package(conn, ident)
    (folder / 'cv.pdf').unlink()
    if via_log:
        applications.log_submission(conn, folder, 'applied', 'test', agent='codex')
        assert 'status: applied' in (folder / 'submission.log').read_text()
    else:
        db.set_status(conn, ident, 'applied', agent='codex')
    assert conn.execute('SELECT status FROM jobs').fetchone()[0] == 'applied'
    assert applications.resume(conn) == []


def test_needs_user_preserves_approval_and_can_resume_send(approve_package):
    conn = db.connect()
    ident = record(conn)
    folder = approve_package(conn, ident)
    binding = approval.validated(folder)
    applications.log_submission(conn, folder, 'needs_user', 'test', 'CAPTCHA')
    assert conn.execute('SELECT status,approval_hash FROM jobs').fetchone()[:] == ('needs_user', binding)
    assert approval.before_send(conn, ident)['ok']
    (folder / 'cv.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError):
        approval.before_send(conn, ident)


def test_cli_human_approval_and_manual_submission(approve_package):
    conn = db.connect()
    ident = record(conn)
    folder = approve_package(conn, ident)
    db.set_status(conn, ident, 'reviewed')
    cli.main(['set-status', ident, 'approved', '--agent', 'human'])
    assert approval.before_send(conn, ident)['ok']
    db.set_status(conn, ident, 'needs_user')
    (folder / 'cv.pdf').unlink()
    cli.main(['set-status', ident, 'applied', '--agent', 'human'])
    assert conn.execute('SELECT status,assigned_agent FROM jobs').fetchone()[:] == ('applied', 'human')


def test_manual_log_submission_without_approval(approve_package):
    conn = db.connect()
    ident = record(conn)
    folder = approve_package(conn, ident)
    db.set_status(conn, ident, 'needs_user')
    (folder / '.review-binding.json').unlink()
    cli.main(['log-applied', str(folder), 'applied', 'test', '--agent', 'human'])
    assert conn.execute('SELECT status FROM jobs').fetchone()[0] == 'applied'


@pytest.mark.parametrize('failure', ['pdf', 'review', 'changed'])
def test_review_batch_continues_after_one_folder_fails(approve_package, monkeypatch, capsys, failure):
    conn = db.connect()
    good = approve_package(conn, record(conn))
    job = dict(source='test', external_id='2', url='https://example.com/2',
               title='Analista de datos', company='Other', description='SQL')
    db.insert_job(conn, job)
    bad = approve_package(conn, db.job_id(job))
    for folder in (good, bad):
        (folder / '.review-binding.json').unlink()
    if failure == 'pdf':
        (bad / 'cv.pdf').unlink()

    def review(*args, **kwargs):
        for folder in (bad, good):
            (folder / 'review.json').write_text('{"verdict":"approve"}', encoding='utf-8')
        if failure == 'review':
            (bad / 'review.json').unlink()
        if failure == 'changed':
            (bad / 'cv.md').write_text('changed', encoding='utf-8')
        return {'code': 0, 'output': 'REVIEW OUTPUT', 'limit_hit': False}

    monkeypatch.setattr(engines, 'run', review)
    with pytest.raises(SystemExit) as result:
        cli.main(['review', str(bad), str(good)])
    assert result.value.code == 1
    assert approval.validated(good)
    assert not (bad / '.review-binding.json').exists()
    output = capsys.readouterr().out
    assert 'REVIEW OUTPUT' in output and str(bad.name) in output


def test_connect_does_not_take_write_lock(tmp_path):
    file = tmp_path / 'shared.db'
    conn = db.connect(file)
    conn.execute('BEGIN IMMEDIATE')
    other = db.connect(file)
    assert other.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] == 0
    other.close()
    conn.rollback()
    conn.close()


def test_cli_reports_database_lock(monkeypatch, capsys):
    def locked():
        raise sqlite3.OperationalError('database is locked')
    monkeypatch.setattr(cli, 'connect', locked)
    with pytest.raises(SystemExit) as result:
        cli.main(['stats'])
    assert result.value.code == 2
    assert 'ocupada' in capsys.readouterr().err
