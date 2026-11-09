import unicodedata

import pytest

from check_offer.models import QuoteStatus
from check_offer.quotes import check_quote


CV_TEXT = """Ana Ejemplo
Ingeniería en Informática.
Desarrollo backend con Python y Django.
Experiencia con C++ y JavaScript.
Certificación oficial en   bases de datos.
"""

GENERIC_WORDS = {"desarrollo", "experiencia"}


def check(quote, cv_text=CV_TEXT):
    return check_quote(quote, cv_text, GENERIC_WORDS)


def test_accepts_a_literal_quote():
    assert check("backend con Python") == QuoteStatus.VALID


def test_rejects_an_invented_quote():
    assert check("Kubernetes en producción") == QuoteStatus.NOT_FOUND


def test_ignores_case():
    assert check("BACKEND CON PYTHON") == QuoteStatus.VALID


def test_ignores_line_breaks():
    assert check("Informática. Desarrollo backend") == QuoteStatus.VALID


def test_ignores_repeated_spaces():
    assert check("oficial en bases de datos") == QuoteStatus.VALID


def test_matches_composed_and_decomposed_accents():
    decomposed = unicodedata.normalize("NFD", "Ingeniería en Informática")

    assert check(decomposed) == QuoteStatus.VALID


def test_matches_pdf_ligatures():
    cv_with_ligature = "Certiﬁcación oficial"

    assert check("Certificación oficial", cv_with_ligature) == QuoteStatus.VALID


def test_ignores_accents():
    assert check("Ingenieria en Informatica") == QuoteStatus.VALID


@pytest.mark.parametrize("quote", [None, "", "   "])
def test_detects_an_empty_quote(quote):
    assert check(quote) == QuoteStatus.EMPTY


def test_accepts_a_valuable_single_word():
    assert check("Python") == QuoteStatus.VALID


def test_a_word_does_not_match_inside_a_longer_word():
    assert check("Java") == QuoteStatus.NOT_FOUND


def test_accepts_a_single_word_with_symbols():
    assert check("C++") == QuoteStatus.VALID


@pytest.mark.parametrize("quote", ["desarrollo", "Experiencia", "desarrollo."])
def test_rejects_a_single_generic_word(quote):
    assert check(quote) == QuoteStatus.GENERIC_WORD


def test_generic_words_do_not_apply_with_two_words():
    assert check("Desarrollo backend") == QuoteStatus.VALID
