import markdown
import warnings
import subprocess
from pathlib import Path
import pytest
from bs4 import BeautifulSoup

from gmaj import render_cv


def test_xml_declaration_is_removed_without_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        clean = render_cv.sanitize_html('<?xml version="1.0"?><p>CV</p>')
    assert not caught
    assert clean == '<p>CV</p>'


def rendered_html(tmp_path, monkeypatch, content, **options):
    src = tmp_path / 'cv.md'
    src.write_text(content, encoding='utf-8')
    monkeypatch.setattr(render_cv, 'find_browser', lambda: 'browser')
    captured = []
    def run(cmd, **kwargs):
        captured.append(src.with_suffix('.html').read_text(encoding='utf-8'))
        assert cmd[-1] == src.with_suffix('.html').as_uri()
        assert kwargs['check'] is True
        assert '--blink-settings=scriptEnabled=false' not in cmd
        Path(next(arg.split('=', 1)[1] for arg in cmd if arg.startswith('--print-to-pdf='))).write_bytes(b'%PDF-1.4 test')
    monkeypatch.setattr(render_cv.subprocess, 'run', run)
    assert render_cv.render(src, **options) == src.with_suffix('.pdf')
    assert not src.with_suffix('.html').exists()
    return BeautifulSoup(captured[0], 'html.parser')


@pytest.mark.parametrize('empty', [False, True])
@pytest.mark.parametrize('previous_pdf', [False, True])
def test_render_rejects_missing_or_empty_pdf(tmp_path, monkeypatch, empty, previous_pdf):
    src = tmp_path / 'cv.md'
    src.write_text('# Candidate', encoding='utf-8')
    out = tmp_path / 'output.pdf'
    if previous_pdf:
        out.write_bytes(b'%PDF-1.4 old')
    monkeypatch.setattr(render_cv, 'find_browser', lambda: 'browser')

    def run(cmd, **kwargs):
        assert not out.exists()
        if empty:
            out.touch()
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(render_cv.subprocess, 'run', run)
    with pytest.raises(RuntimeError, match='^El navegador no generó el PDF$'):
        render_cv.render(src, out=out)
    assert not src.with_suffix('.html').exists()


def test_render_removes_active_content_and_adds_csp(tmp_path, monkeypatch):
    soup = rendered_html(tmp_path, monkeypatch, '''# Candidate
<script>alert(1)</script><iframe src="https://example.com"><p>frame</p></iframe>
<object data="https://example.com"><b>object</b></object>
<img src=http://example.com onerror="alert(1)">
<p onclick="alert(1)" style="background:url(https://example.com)">Text</p>
<a href="javascript:alert(1)">bad</a><a href="&#106;avascript:alert(2)">bad2</a>
<svg><a href="https://example.com">svg</a></svg>
<meta http-equiv="refresh" content="0;url=https://example.com">
<link rel="stylesheet" href="https://example.com">
<form action="https://example.com"><input autofocus onfocus="alert(1)"></form>
''')
    assert not soup.body.find_all(['script', 'iframe', 'object', 'img', 'svg', 'meta', 'link', 'form', 'input'])
    assert not any(tag.attrs for tag in soup.body.find_all(True))
    assert soup.head.find('meta', attrs={'http-equiv': 'Content-Security-Policy'})['content'] == "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"


def test_normal_cv_preserves_markup_and_layout(tmp_path, monkeypatch):
    content = '''# Candidate

Email: [contact](mailto:candidate@example.com) | [web](https://example.com)

## Experience

**Role** at *Company*  
Description

- First achievement
- Second achievement

<table><tr><th>Skill</th><td>Python</td></tr></table>
'''
    soup = rendered_html(tmp_path, monkeypatch, content, page='A4')
    expected = BeautifulSoup(markdown.markdown(content, extensions=['nl2br']), 'html.parser')
    assert soup.body.decode_contents() == str(expected)
    assert soup.style.string == render_cv.CSS % {'page': 'A4'}


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'data:text/html,test', '//example.com',
                               'file:///etc/passwd', 'vbscript:test', 'java\nscript:alert(1)'])
def test_only_allowed_link_schemes(url):
    soup = BeautifulSoup(render_cv.sanitize_html(f'<a href="{url}" title="test">link</a>'), 'html.parser')
    assert soup.a.attrs == {}


def test_page_size_cannot_inject_html(tmp_path, monkeypatch):
    soup = rendered_html(tmp_path, monkeypatch, '# Candidate', page='</style><script>alert(1)</script>')
    assert not soup.script
    assert soup.style.string == render_cv.CSS % {'page': 'Letter'}


@pytest.mark.parametrize('payload', [
    '<![CDATA[><img src=x onerror=alert(1)><meta http-equiv=refresh content="0;url=https://example.com">]]>',
    '<?test ><meta http-equiv=refresh content="0;url=https://example.com">?>',
    '<!DOCTYPE html [><script>alert(1)</script>]>',
    '<!--[if IE]><img src=x onerror=alert(1)><meta http-equiv=refresh><![endif]-->',
])
def test_special_nodes_cannot_escape_sanitizer(payload, tmp_path, monkeypatch):
    clean = render_cv.sanitize_html(payload).lower()
    for forbidden in ('<meta http-equiv', '<img', 'onerror', '<script', '<!doctype', '<![cdata', '<?'):
        assert forbidden not in clean
    soup = rendered_html(tmp_path, monkeypatch, payload)
    assert not soup.body.find(['meta', 'img', 'script'])


def test_fixture_and_passive_markdown_are_preserved(user_dir):
    text = (user_dir / 'variants/cv_datos_es.md').read_text(encoding='utf-8')
    raw = markdown.markdown(text, extensions=['nl2br'])
    assert render_cv.sanitize_html(raw) == str(BeautifulSoup(raw, 'html.parser'))
    raw = '<pre><code>x</code></pre><blockquote>q</blockquote><sub>x</sub><sup>x</sup><u>x</u><s>x</s><del>x</del><hr/><a href="#anchor">x</a>'
    assert render_cv.sanitize_html(raw) == str(BeautifulSoup(raw, 'html.parser'))
