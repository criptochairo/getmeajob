from gmaj.cv_language import cv_language


def test_english_posting():
    assert cv_language('Legal Operations Specialist', 'We are looking for a specialist to join our team with experience in contracts.')[0] == 'en'


def test_spanish_posting():
    assert cv_language('Analista de Cumplimiento', 'Buscamos un analista con experiencia en PLD para nuestro equipo de la empresa.')[0] == 'es'


def test_spanish_posting_requests_english_cv():
    desc = 'Buscamos abogado bilingüe para el equipo. Envía tu CV en inglés a la dirección indicada.'
    assert cv_language('Abogado Corporativo', desc) == ('en', 'posting asks for CV in English')


def test_english_posting_requests_english_resume():
    assert cv_language('Paralegal', 'Please submit your resume in English.')[0] == 'en'


def test_unclear_defaults_to_english():
    assert cv_language('Legal Tech', '')[0] == 'en'
