import argparse
import sys
from pathlib import Path

from check_offer.constants import (
    EXIT_INPUT_ERROR,
    EXIT_INVALID_CONTRACT,
    EXIT_OK,
    GENERIC_WORDS_EN,
    GENERIC_WORDS_ES,
)
from check_offer.convert import read_text_file
from check_offer.exceptions import ContractError, InputError
from check_offer.matching import run_matching
from check_offer.validate import parse_analysis


def main(argv):
    """Validate an analysis against a CV and write the report.

    Returns EXIT_OK when the analysis was processed, even if quotes were rejected:
    deciding whether to retry belongs to the hook, which reads the report.
    Returns EXIT_INVALID_CONTRACT or EXIT_INPUT_ERROR, and writes nothing, when the
    analysis is invalid or an input file cannot be read.
    """
    parser = argparse.ArgumentParser(prog="check_offer")
    parser.add_argument("analysis", type=Path)
    parser.add_argument("cv", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("rejected_log", type=Path)
    args = parser.parse_args(argv)

    try:
        raw_analysis = read_text_file(args.analysis)
        cv_text = read_text_file(args.cv)
    except InputError as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    try:
        requirements = parse_analysis(raw_analysis)
    except ContractError as error:
        print(f"Invalid analysis: {error}", file=sys.stderr)
        return EXIT_INVALID_CONTRACT

    report = run_matching(
        requirements, cv_text, GENERIC_WORDS_ES | GENERIC_WORDS_EN
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    _record_rejected_quotes(report.rejected_quotes, args.rejected_log)
    return EXIT_OK


def _record_rejected_quotes(rejected_quotes, log_path):
    """Print each rejected quote and append it to the log, one JSON per line.

    The log file is created only when there is something to record.
    """
    if not rejected_quotes:
        return

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        for rejected in rejected_quotes:
            print(
                f"Rejected quote ({rejected.quote_status.value}): "
                f"{rejected.requirement}: {rejected.quote}"
            )
            log.write(rejected.model_dump_json() + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
