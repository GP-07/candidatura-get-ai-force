from pathlib import Path

import pytest

from check_offer.convert import convert_file, main
from check_offer.exceptions import InputError


FIXTURES = Path(__file__).parent / "fixtures"
TEXT = "Ingeniería en Informática\nBackend con Python\n"


@pytest.fixture
def destination(tmp_path):
    return tmp_path / "private" / "converted" / "cv.txt"


@pytest.mark.parametrize("name", ["cv.md", "cv.txt", "CV.TXT"])
def test_text_files_are_copied_unchanged(tmp_path, destination, name):
    source = tmp_path / name
    source.write_text(TEXT, encoding="utf-8")

    convert_file(source, destination)

    assert destination.read_text(encoding="utf-8") == TEXT


def test_a_pdf_with_text_is_converted(destination):
    convert_file(FIXTURES / "with_text.pdf", destination)

    assert destination.read_text(encoding="utf-8").strip() == "Backend con Python"


def test_a_pdf_without_text_is_rejected(destination):
    """A scanned PDF has no text to quote from, so it must not produce an empty CV."""
    with pytest.raises(InputError, match="no extractable text"):
        convert_file(FIXTURES / "no_text.pdf", destination)

    assert not destination.exists()


def test_a_corrupt_pdf_is_rejected(tmp_path, destination):
    source = tmp_path / "corrupt.pdf"
    source.write_bytes(b"this is not a pdf")

    with pytest.raises(InputError):
        convert_file(source, destination)

    assert not destination.exists()


def test_an_unsupported_extension_is_rejected(tmp_path, destination):
    source = tmp_path / "cv.docx"
    source.write_text(TEXT, encoding="utf-8")

    with pytest.raises(InputError, match=r"\.docx"):
        convert_file(source, destination)


def test_a_missing_source_is_rejected(tmp_path, destination):
    with pytest.raises(InputError):
        convert_file(tmp_path / "missing.txt", destination)


def test_a_text_file_that_is_not_utf8_is_rejected(tmp_path, destination):
    source = tmp_path / "cv.txt"
    source.write_bytes("Ingeniería".encode("latin-1"))

    with pytest.raises(InputError):
        convert_file(source, destination)


def test_main_returns_zero_when_the_file_is_converted(tmp_path, destination):
    source = tmp_path / "cv.txt"
    source.write_text(TEXT, encoding="utf-8")

    exit_code = main([str(source), str(destination)])

    assert exit_code == 0
    assert destination.exists()


def test_main_reports_an_input_error_and_returns_one(tmp_path, destination, capsys):
    exit_code = main([str(tmp_path / "missing.txt"), str(destination)])

    assert exit_code == 1
    assert capsys.readouterr().err != ""
    assert not destination.exists()
