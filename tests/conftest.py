import pytest


@pytest.fixture
def paths(tmp_path):
    (tmp_path / "cv.txt").write_text(
        "Desarrollo backend con Python y Django.", encoding="utf-8"
    )
    return {
        "analysis": tmp_path / "analysis.json",
        "cv": tmp_path / "cv.txt",
        "report": tmp_path / "report.json",
        "log": tmp_path / "private" / "rejected_quotes.jsonl",
    }
