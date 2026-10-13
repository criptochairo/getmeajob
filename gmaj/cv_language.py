"""Decide which language the CV / cover letter must be sent in.

Rule: many recruiters discard CVs in the wrong language.
  1. If the posting explicitly asks for the CV in a language -> that language.
  2. Otherwise -> the language the posting is written in.
  3. If the posting's language can't be told apart -> English (safer for international roles).
"""
import re

EXPLICIT_EN = [
    r'(resume|cv|curriculum)[^.\n]{0,40}\bin english\b', r'\benglish (resume|cv)\b',
    r'(cv|curr[ií]culum)[^.\n]{0,30}\ben ingl[eé]s\b', r'\bcv en ingl[eé]s\b',
]
EXPLICIT_ES = [r'(cv|curr[ií]culum)[^.\n]{0,30}\ben espa[nñ]ol\b', r'(resume|cv)[^.\n]{0,40}\bin spanish\b']

EN_WORDS = {'the', 'and', 'with', 'you', 'our', 'will', 'for', 'experience', 'team', 'skills', 'of', 'to', 'we', 'are'}
ES_WORDS = {'el', 'la', 'los', 'las', 'con', 'para', 'experiencia', 'equipo', 'del', 'que', 'en', 'de', 'nuestro', 'somos'}


def detect_text_language(text):
    words = re.findall(r"[a-záéíóúñü]+", (text or '').lower())
    en = sum(w in EN_WORDS for w in words)
    es = sum(w in ES_WORDS for w in words)
    if en == es:
        return None
    return 'en' if en > es else 'es'


def cv_language(title, description):
    text = f"{title or ''}\n{description or ''}".lower()
    if any(re.search(p, text) for p in EXPLICIT_EN):
        return 'en', 'posting asks for CV in English'
    if any(re.search(p, text) for p in EXPLICIT_ES):
        return 'es', 'posting asks for CV in Spanish'
    lang = detect_text_language(text)
    if lang:
        return lang, f'posting written in {lang}'
    return 'en', 'language unclear; defaulting to English'
