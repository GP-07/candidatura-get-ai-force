import subprocess
from unittest.mock import Mock

import pytest

from check_offer.exceptions import DockerUnavailableError
from check_offer.hook import handle_event, run_validate
from helpers import (
    analysis_written_event,
    attempts_file,
    completed_process,
    write_event,
    write_report,
)


PROCESSED = (0, "")
INVALID_CONTRACT = (2, "requirements.0.score is invalid")
INPUT_ERROR = (1, "Cannot read private/converted/cv.txt")
REJECTED_QUOTE = {
    "requirement": "Experiencia con Kubernetes",
    "quote": "Kubernetes en producción",
    "original_score": 1.0,
    "quote_status": "not_found",
}


def test_ignores_other_files(project):
    """Writing any file other than the analysis must not run the validation."""
    validate = Mock()

    exit_code = handle_event(write_event(project / "README.md"), project, validate)

    assert exit_code == 0
    validate.assert_not_called()


def test_ignores_an_unreadable_event(project):
    """An event that cannot be parsed must not block the agent's other writes."""
    validate = Mock()

    exit_code = handle_event("no es json", project, validate)

    assert exit_code == 0
    validate.assert_not_called()


def test_an_analysis_without_rejections_passes(project):
    """A clean analysis passes and never creates the attempts file."""
    write_report(project, [])
    validate = Mock(return_value=PROCESSED)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 0
    assert not attempts_file(project).exists()


def test_the_first_rejection_blocks_and_explains_the_error(project, capsys):
    """The first rejected quote blocks the agent and uses its only retry.

    The agent receives the quote and the reason, so it can correct the analysis.
    """
    write_report(project, [REJECTED_QUOTE])
    validate = Mock(return_value=PROCESSED)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 2
    assert attempts_file(project).exists()
    message = capsys.readouterr().err
    assert "Kubernetes en producción" in message
    assert "not_found" in message


def test_the_second_rejection_is_accepted_and_clears_the_attempt(project):
    """With the retry already used, the report stands with those quotes lowered to 0."""
    write_report(project, [REJECTED_QUOTE])
    attempts_file(project).touch()
    validate = Mock(return_value=PROCESSED)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 0
    assert not attempts_file(project).exists()


def test_a_clean_retry_clears_the_attempt(project):
    """A retry that fixes every quote passes and removes the temporary file."""
    write_report(project, [])
    attempts_file(project).touch()
    validate = Mock(return_value=PROCESSED)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 0
    assert not attempts_file(project).exists()


def test_a_first_invalid_contract_blocks_and_uses_the_retry(project, capsys):
    """An analysis with an invalid format can be corrected once."""
    validate = Mock(return_value=INVALID_CONTRACT)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 2
    assert attempts_file(project).exists()
    assert "requirements.0.score" in capsys.readouterr().err


def test_a_second_invalid_contract_tells_the_agent_to_stop(project, capsys):
    """If the format is still invalid, there is no report and the agent must stop."""
    attempts_file(project).touch()
    validate = Mock(return_value=INVALID_CONTRACT)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 2
    assert not attempts_file(project).exists()
    assert "do not retry" in capsys.readouterr().err.lower()


def test_an_input_error_does_not_use_the_retry(project, capsys):
    """A missing input file is not the agent's mistake, so it keeps its retry."""
    validate = Mock(return_value=INPUT_ERROR)

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 2
    assert not attempts_file(project).exists()
    assert "converted/cv.txt" in capsys.readouterr().err


def test_unavailable_docker_is_reported_and_does_not_use_the_retry(project, capsys):
    """Docker being down is not the agent's mistake, but the user must find out."""
    validate = Mock(side_effect=DockerUnavailableError("Cannot connect"))

    exit_code = handle_event(analysis_written_event(project), project, validate)

    assert exit_code == 2
    assert not attempts_file(project).exists()
    assert "Docker" in capsys.readouterr().err


def test_run_validate_uses_paths_relative_to_the_project(project, monkeypatch):
    """Relative paths let the repository work after being cloned on another machine."""
    subprocess_run = Mock(return_value=completed_process(0))
    monkeypatch.setattr(subprocess, "run", subprocess_run)

    result = run_validate(project)

    assert result == (0, "")
    command = subprocess_run.call_args.args[0]
    assert command == [
        "docker",
        "compose",
        "run",
        "--rm",
        "-T",
        "validate",
        "private/analysis.json",
        "private/converted/cv.txt",
        "private/report.json",
        "private/rejected_quotes.jsonl",
    ]
    assert subprocess_run.call_args.kwargs["cwd"] == project


def test_run_validate_detects_a_stopped_docker(project, monkeypatch):
    """Docker failing to respond raises a specific error, not a validation result."""
    monkeypatch.setattr(subprocess, "run", Mock(return_value=completed_process(1, "down")))

    with pytest.raises(DockerUnavailableError):
        run_validate(project)


def test_run_validate_detects_a_missing_docker(project, monkeypatch):
    """A machine without Docker installed gets the same specific error."""
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=FileNotFoundError("docker")))

    with pytest.raises(DockerUnavailableError):
        run_validate(project)
