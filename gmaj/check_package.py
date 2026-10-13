"""Deterministic (no-LLM) checks for an application package. Writes <dir>/check.json.

Contact data and forbidden strings come from user/profile.yaml (personal.email, personal.phone,
cv_policy.forbidden_strings, cv_policy.omit_employers). Exit code 1 if any package fails.
"""
import json
import re

from . import config, paths
from .cv_language import detect_text_language


def numbers(text):
    """Percentages and standalone counts that a reviewer would check against the profile."""
    return set(re.findall(r'\b\d+(?:[.,]\d+)?\s?%|\b\d{2,3}\+?(?=\s(?:properties|propiedades|people|personas|members|integrantes|'
                          r'companies|empresas|years|años|clients|clientes|projects|proyectos))', text))


def digits(value):
    return re.sub(r'\D', '', str(value or ''))


def rules():
    profile = config.profile()
    policy = profile.get('cv_policy') or {}
    personal = profile.get('personal') or {}
    forbidden = [str(s).lower() for s in (policy.get('forbidden_strings') or []) + (policy.get('omit_employers') or []) if str(s).strip()]
    contact = [c for c in (personal.get('email'), personal.get('phone')) if c]
    text = paths.user('profile.yaml').read_text(encoding='utf-8') + paths.user('answers.yaml').read_text(encoding='utf-8')
    return forbidden, contact, text


def has_contact(text, value):
    """Phones may be formatted differently in the CV: compare digits for phones, plain text for the rest."""
    if '@' in value or not digits(value):
        return value.lower() in text.lower()
    return digits(value)[-8:] in digits(text)


def check(folder, forbidden=None, contact=None, profile_text=None):
    if forbidden is None:
        forbidden, contact, profile_text = rules()
    job = (folder / 'job.md').read_text(encoding='utf-8')
    lang = re.search(r'cv_language:\s*(\w+)', job).group(1)
    issues = []
    for name in ('cv.md', 'cover.md'):
        f = folder / name
        if not f.exists():
            issues.append(f'{name} missing')
            continue
        text = f.read_text(encoding='utf-8')
        low = text.lower()
        detected = detect_text_language(text)
        if detected and detected != lang:
            issues.append(f'{name}: language {detected}, expected {lang}')
        issues += [f'{name}: forbidden "{w}"' for w in forbidden if w in low]
        if '{{' in text:
            issues.append(f'{name}: unfilled placeholder')
        if name == 'cv.md':
            issues += [f'cv.md: contact missing "{c}"' for c in contact if not has_contact(text, c)]
        known = {x.replace(',', '.') for x in re.findall(r'\d+(?:[.,]\d+)?', profile_text)}
        for n in numbers(text):
            core = re.search(r'\d+(?:[.,]\d+)?', n).group().replace(',', '.')
            if core not in known:
                issues.append(f'{name}: number "{n}" not found in profile')
        if name == 'cover.md' and len(text.split()) > 260:
            issues.append(f'cover.md: {len(text.split())} words (>250)')
    try:
        ans = json.loads((folder / 'answers.json').read_text(encoding='utf-8'))
        if ans.get('cv_language') and ans['cv_language'] != lang:
            issues.append('answers.json: cv_language mismatch')
    except Exception as e:
        issues.append(f'answers.json invalid: {e}')
    result = {'ok': not issues, 'cv_language': lang, 'issues': issues}
    (folder / 'check.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    return result
