import argparse
import subprocess
import sys
from pathlib import Path

from check_offer.constants import (
    EXIT_INPUT_ERROR,
    EXIT_OK,
    PDF_EXTENSION,
    TEXT_EXTENSIONS,
)
from check_offer.exceptions import InputError


def read_text_file(path):
    """Return the content of a UTF-8 text file.

    Raises InputError if the file is missing, unreadable or not valid UTF-8.
    Other encodings are rejected on purpose: guessing one could corrupt accents
    without warning and make correct quotes fail.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise InputError(f"Cannot read {path}: {error}") from error


def convert_file(source, destination):
    """Write the text of a .md, .txt or .pdf file to the destination.

    The validator reads this converted text, so quotes are compared against the
    same text the agent read. Nothing is written if the conversion fails.

    Raises InputError for unsupported extensions and unreadable files.
    """
    extension = source.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        text = read_text_file(source)
    elif extension == PDF_EXTENSION:
        text = _extract_pdf_text(source)
    else:
        raise InputError(f"Unsupported file type: {extension}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _extract_pdf_text(source):
    """Return the text of a PDF using pdftotext.

    Failure is decided by the exit code, because pdftotext also prints warnings
    for PDFs that it can read.

    Special case: a PDF without text, such as a scan, raises InputError instead of
    producing an empty CV.
    """
    result = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(source), "-"],
        capture_output=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise InputError(f"Cannot read PDF {source}: {result.stderr.strip()}")
    if not result.stdout.strip():
        raise InputError(f"PDF {source} has no extractable text")
    return result.stdout


def main(argv):
    """Convert one input file. Returns EXIT_OK, or EXIT_INPUT_ERROR on failure."""
    parser = argparse.ArgumentParser(prog="check_offer.convert")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)

    try:
        convert_file(args.source, args.destination)
    except InputError as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
