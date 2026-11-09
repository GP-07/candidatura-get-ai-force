import json
import subprocess

from check_offer.cli import main


def analysis(score, quote):
    return {
        "requirements": [
            {
                "requirement": "Experiencia con Python",
                "score": score,
                "quote": quote,
                "justification": "Justificación del modelo.",
            }
        ]
    }


def run_cli(paths):
    return main(
        [
            str(paths["analysis"]),
            str(paths["cv"]),
            str(paths["report"]),
            str(paths["log"]),
        ]
    )


def run(paths, content):
    raw = content if isinstance(content, str) else json.dumps(content)
    paths["analysis"].write_text(raw, encoding="utf-8")
    return run_cli(paths)


def read_report(paths):
    return json.loads(paths["report"].read_text(encoding="utf-8"))


def read_log(paths):
    lines = paths["log"].read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def attempts_file(project):
    return project / "private" / ".analysis_attempts"


def write_event(path):
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(path)}})


def analysis_written_event(project):
    return write_event(project / "private" / "analysis.json")


def write_report(project, rejected_quotes):
    report = {"summary": {}, "requirements": [], "rejected_quotes": rejected_quotes}
    (project / "private" / "report.json").write_text(json.dumps(report), encoding="utf-8")


def completed_process(returncode, stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout="", stderr=stderr)
