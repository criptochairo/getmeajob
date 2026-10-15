"""Entry-level candidates (student / new_grad / first_job): validation, prefilter and package checks."""
import shutil
from datetime import date

import pytest
import yaml

from conftest import ROOT, load_config
from gmaj import check_package, prefilter, validate

ENTRY_PROFILE = ROOT / 'tests' / 'fixtures' / 'user_entry' / 'profile.yaml'


def use_entry_profile(user_dir):
    shutil.copy(ENTRY_PROFILE, user_dir / 'profile.yaml')


def edit_yaml(path, change):
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    change(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')


def test_entry_profile_validates_without_experience(user_dir):
    use_entry_profile(user_dir)
    edit_yaml(user_dir / 'profile.yaml', lambda d: d.update(experience=[]))
    result = validate.check(only=['profile', 'answers'])
    assert result['ok'], result['problems']


def test_experienced_profile_still_requires_experience(user_dir):
    edit_yaml(user_dir / 'profile.yaml', lambda d: d.update(experience=[]))
    assert any('falta experience' in p for p in validate.check(only=['profile', 'answers'])['problems'])


def test_invalid_career_stage(user_dir):
    edit_yaml(user_dir / 'profile.yaml', lambda d: d.update(career_stage='intern'))
    assert any('career_stage' in p for p in validate.check(only=['profile'])['problems'])


@pytest.mark.parametrize('identity,ok', [
    ({'age': 17}, False),
    ({'age': 18}, True),
    ({'date_of_birth': '2010-01-01', 'age': 30}, False),   # the date wins over a stale age
    ({'age': None, 'date_of_birth': ''}, True),             # unknown age is not blocked here (the interview asks)
])
def test_minimum_age(user_dir, identity, ok):
    edit_yaml(user_dir / 'answers.yaml', lambda d: d['identity'].update(identity))
    problems = validate.check(only=['answers'])['problems']
    assert (not any('18 años' in p for p in problems)) == ok


def test_age_from_birth_date():
    assert validate.age({'date_of_birth': '2008-10-15'}, today=date(2026, 10, 14)) == 17
    assert validate.age({'date_of_birth': '2008-10-14'}, today=date(2026, 10, 14)) == 18


def entry_config(**salary):
    config = load_config()
    config['entry_level'] = {'enabled': True, 'max_years_required': 2,
                             'internship_keywords': ['intern', 'becario', 'practicante', 'trainee']}
    config['exclusions']['title_keywords'] = ['intern', 'internship', 'becario', 'practicante', 'trainee']
    config['salary'].update(salary)
    return config


@pytest.mark.parametrize('changes,expected', [
    ({'title': 'Becario de datos'}, 'filtered'),
    ({'title': 'Data Intern', 'salary_min': 8000, 'salary_currency': 'MXN', 'salary_period': 'month'}, 'filtered'),
    ({'title': 'Data Intern', 'salary_min': 4000, 'salary_currency': 'MXN', 'salary_period': 'month'}, 'discarded'),
    ({'salary_min': 8000, 'salary_currency': 'MXN', 'salary_period': 'month'}, 'discarded'),   # not an internship: normal floor
    ({'description': 'Requisitos: 3+ años de experiencia en SQL'}, 'discarded'),
    ({'description': 'Deseable 1-2 años de experiencia o recién egresado'}, 'filtered'),
    ({'description': 'Minimum 5 years of experience'}, 'discarded'),
    ({'description': 'Contamos con más de 10 años de experiencia en el mercado. Sin experiencia necesaria'}, 'filtered'),
    ({'description': 'Experiencia mínima de 4 años'}, 'discarded'),
])
def test_entry_prefilter(changes, expected):
    job = dict(title='Data Analyst', company='Example', work_mode='remote', description='', location='', salary_min=None)
    job.update(changes)
    assert prefilter.evaluate(job, entry_config(internship_floor_month=6000))[0] == expected


def test_years_filter_off_for_experienced_profiles():
    job = dict(title='Data Analyst', company='Example', work_mode='remote', description='5 years of experience', location='')
    assert prefilter.evaluate(job, load_config())[0] == 'filtered'


def test_claim_limits_and_issues(user_dir):
    use_entry_profile(user_dir)
    limits = check_package.claim_limits(yaml.safe_load(ENTRY_PROFILE.read_text(encoding='utf-8')))
    assert limits == {'max_years': 1, 'degree': False, 'coursework': True, 'license': False}
    ok = 'Pasante de Ingeniería en Sistemas con 1 año de experiencia en soporte.'
    assert check_package.claim_issues('cv.md', ok, limits) == []
    bad = 'Ingeniero titulado con 3 años de experiencia y cédula profesional.'
    issues = ' '.join(check_package.claim_issues('cv.md', bad, limits))
    assert '3 years' in issues and 'titulado' in issues and 'cédula profesional' in issues
