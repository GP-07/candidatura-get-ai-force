"""Claude Code hook that validates the analysis as soon as the agent writes it.

This module runs on the host, outside Docker, so it can only import the standard
library and modules of this package that do not depend on pydantic.
"""

import json
import subprocess
import sys
import unicodedata
from pathlib import Path

from check_offer.constants import (
    ANALYSIS_PATH,
    ATTEMPTS_PATH,
    CV_TEXT_PATH,
    EXIT_BLOCK_AGENT,
    EXIT_INVALID_CONTRACT,
    EXIT_OK,
    REJECTED_LOG_PATH,
    REPORT_PATH,
)
from check_offer.exceptions import DockerUnavailableError


def handle_event(raw_event, project_dir, validate):
    """Validate the analysis if this event wrote it, and return the hook's exit code.

    Returning EXIT_BLOCK_AGENT sends the message printed to stderr to the agent.

    The agent has one retry, tracked by a temporary file that exists only between
    the first rejection and the retry:
    - With rejected quotes, the first attempt blocks. The second one is accepted,
      since the validator already lowered those scores to 0.
    - With an invalid format, the first attempt blocks. The second one tells the
      agent to stop, because there is no report to accept.

    Special cases:
    - Other files and unreadable events are ignored, so they never block the agent.
    - Missing input files and Docker being down are reported without using the
      retry, because they are not mistakes of the agent.
    """
    if not _is_analysis_write(raw_event, project_dir):
        return EXIT_OK

    try:
        exit_code, error = validate(project_dir)
    except DockerUnavailableError as docker_error:
        return _block_agent(f"Docker is not available: {docker_error}")

    if exit_code == EXIT_INVALID_CONTRACT:
        return _handle_invalid_contract(error, project_dir)
    if exit_code != EXIT_OK:
        return _block_agent(f"The validation could not run: {error}")
    return _handle_processed_analysis(project_dir)


def run_validate(project_dir):
    """Run the validator through Docker Compose and return (exit code, stderr).

    It uses paths relative to the project, so the repository works on any machine.

    Raises DockerUnavailableError if Docker is not installed or not running.
    """
    try:
        docker_info = subprocess.run(
            ["docker", "info"], capture_output=True, encoding="utf-8", cwd=project_dir
        )
        if docker_info.returncode != 0:
            raise DockerUnavailableError(docker_info.stderr.strip())

        result = subprocess.run(
            [
                "docker",
                "compose",
                "--progress",
                "quiet",
                "run",
                "--rm",
                "-T",
                "validate",
                ANALYSIS_PATH,
                CV_TEXT_PATH,
                REPORT_PATH,
                REJECTED_LOG_PATH,
            ],
            capture_output=True,
            encoding="utf-8",
            cwd=project_dir,
        )
    except OSError as error:
        raise DockerUnavailableError(str(error)) from error
    return result.returncode, result.stderr


def _is_analysis_write(raw_event, project_dir):
    """Return whether the event is a write to the analysis file.

    Paths are compared in NFC form because macOS can spell the same accented
    character in two ways.
    """
    try:
        file_path = json.loads(raw_event)["tool_input"]["file_path"]
    except (ValueError, KeyError, TypeError):
        return False

    analysis_path = Path(project_dir) / ANALYSIS_PATH
    return _nfc(Path(file_path).resolve()) == _nfc(analysis_path.resolve())


def _nfc(path):
    """Return the path as a string in Unicode NFC form."""
    return unicodedata.normalize("NFC", str(path))


def _handle_invalid_contract(error, project_dir):
    """Give the agent one retry to fix the format, then tell it to stop."""
    attempts = Path(project_dir) / ATTEMPTS_PATH
    if attempts.exists():
        attempts.unlink()
        return _block_agent(
            f"The analysis is still invalid. Do not retry; tell the user: {error}"
        )

    attempts.touch()
    return _block_agent(f"The analysis has an invalid format. Fix it: {error}")


def _handle_processed_analysis(project_dir):
    """Block the first attempt with rejected quotes, and clear the retry otherwise."""
    attempts = Path(project_dir) / ATTEMPTS_PATH
    rejected_quotes = _read_rejected_quotes(project_dir)

    if rejected_quotes and not attempts.exists():
        attempts.touch()
        return _block_agent(_rejection_message(rejected_quotes))

    attempts.unlink(missing_ok=True)
    return EXIT_OK


def _read_rejected_quotes(project_dir):
    """Return the rejected quotes from the report that was just written."""
    report_path = Path(project_dir) / REPORT_PATH
    return json.loads(report_path.read_text(encoding="utf-8"))["rejected_quotes"]


def _rejection_message(rejected_quotes):
    """Tell the agent which quotes failed and how to correct them."""
    lines = [
        "Some quotes were rejected. Copy each one literally from the CV, or set its "
        "score to 0 and its quote to null:"
    ]
    for rejected in rejected_quotes:
        lines.append(
            f"- {rejected['requirement']}: {rejected['quote']} "
            f"({rejected['quote_status']})"
        )
    return "\n".join(lines)


def _block_agent(message):
    """Print a message for the agent and return the exit code that delivers it."""
    print(message, file=sys.stderr)
    return EXIT_BLOCK_AGENT


if __name__ == "__main__":
    sys.exit(handle_event(sys.stdin.read(), Path.cwd(), run_validate))
