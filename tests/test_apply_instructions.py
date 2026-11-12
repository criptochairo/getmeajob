from pathlib import Path


def test_apply_requires_portal_confirmation_and_preserves_pending_tabs():
    prompt = (Path(__file__).resolve().parents[1] / 'prompts/apply.md').read_text(encoding='utf-8')
    submission = prompt.split('6. ', 1)[1].split('7. ', 1)[0]
    assert 'Solo con confirmación del portal' in submission
    assert 'resolver una tarea humana no basta' in submission
    cleanup = prompt.split('7. ', 1)[1]
    assert 'exceptuando las que esperan tareas pendientes del usuario' in cleanup
    for task in ('iniciar sesión', 'crear cuenta', 'assessment', 'CAPTCHA'):
        assert task in cleanup
    assert 'user/inbox/tareas_humanas.md' in cleanup
