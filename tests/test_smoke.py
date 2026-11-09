import shutil


def test_pdftotext_is_available():
    assert shutil.which("pdftotext") is not None
