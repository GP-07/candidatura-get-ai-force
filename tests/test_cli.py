from helpers import analysis, read_log, read_report, run, run_cli


def test_valid_analysis_writes_the_report_and_returns_zero(paths):
    exit_code = run(paths, analysis(1.0, "backend con Python"))

    assert exit_code == 0
    report = read_report(paths)
    assert report["summary"] == {"total": 1, "covered": 1, "gaps": 0}
    assert report["requirements"][0]["quote_status"] == "found"
    assert report["rejected_quotes"] == []


def test_valid_analysis_creates_no_rejection_log(paths):
    run(paths, analysis(1.0, "backend con Python"))

    assert not paths["log"].exists()


def test_a_rejected_quote_still_returns_zero(paths):
    exit_code = run(paths, analysis(1.0, "Kubernetes en producción"))

    assert exit_code == 0
    report = read_report(paths)
    assert report["requirements"][0]["score"] == 0
    assert report["requirements"][0]["quote_status"] == "not_found"


def test_a_rejected_quote_is_printed(paths, capsys):
    run(paths, analysis(1.0, "Kubernetes en producción"))

    output = capsys.readouterr().out
    assert "Kubernetes en producción" in output
    assert "not_found" in output


def test_rejected_quotes_are_appended_to_the_log(paths):
    run(paths, analysis(1.0, "Kubernetes en producción"))
    run(paths, analysis(0.7, "Rust en producción"))

    log = read_log(paths)
    assert [entry["quote"] for entry in log] == [
        "Kubernetes en producción",
        "Rust en producción",
    ]
    assert log[0]["requirement"] == "Experiencia con Python"
    assert log[0]["original_score"] == 1.0
    assert log[0]["quote_status"] == "not_found"


def test_uses_the_generic_words_of_both_languages(paths):
    run(paths, analysis(0.7, "desarrollo"))
    assert read_report(paths)["requirements"][0]["quote_status"] == "generic_word"

    paths["cv"].write_text("Software development", encoding="utf-8")
    run(paths, analysis(0.7, "development"))
    assert read_report(paths)["requirements"][0]["quote_status"] == "generic_word"


def test_invalid_contract_returns_two_and_writes_nothing(paths, capsys):
    exit_code = run(paths, "no es json")

    assert exit_code == 2
    assert capsys.readouterr().err != ""
    assert not paths["report"].exists()
    assert not paths["log"].exists()


def test_a_missing_analysis_returns_one_and_writes_nothing(paths, capsys):
    exit_code = run_cli(paths)

    assert exit_code == 1
    assert capsys.readouterr().err != ""
    assert not paths["report"].exists()


def test_a_missing_cv_returns_one_and_writes_nothing(paths, capsys):
    paths["cv"].unlink()

    exit_code = run(paths, analysis(1.0, "backend con Python"))

    assert exit_code == 1
    assert capsys.readouterr().err != ""
    assert not paths["report"].exists()
