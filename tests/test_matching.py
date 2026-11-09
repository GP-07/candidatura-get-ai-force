from check_offer.models import QuoteStatus, Requirement
from check_offer.matching import run_matching


CV_TEXT = "Desarrollo backend con Python y Django."
GENERIC_WORDS = {"desarrollo"}


def requirement(score, quote, name="Experiencia con Python"):
    return Requirement(
        requirement=name,
        score=score,
        quote=quote,
        justification="Justificación del modelo.",
    )


def report_for(*requirements):
    return run_matching(list(requirements), CV_TEXT, GENERIC_WORDS)


def test_a_valid_quote_keeps_its_score():
    result = report_for(requirement(0.7, "backend con Python")).requirements[0]

    assert result.score == 0.7
    assert result.quote == "backend con Python"
    assert result.justification == "Justificación del modelo."
    assert result.quote_status == QuoteStatus.FOUND


def test_an_invented_quote_lowers_the_score_to_zero():
    result = report_for(requirement(1.0, "Kubernetes en producción")).requirements[0]

    assert result.score == 0
    assert result.quote_status == QuoteStatus.NOT_FOUND


def test_a_missing_quote_lowers_the_score_to_zero():
    result = report_for(requirement(0.4, None)).requirements[0]

    assert result.score == 0
    assert result.quote_status == QuoteStatus.EMPTY


def test_a_generic_quote_lowers_the_score_to_zero():
    result = report_for(requirement(0.7, "desarrollo")).requirements[0]

    assert result.score == 0
    assert result.quote_status == QuoteStatus.GENERIC_WORD


def test_score_zero_keeps_a_real_quote_that_does_not_cover_the_requirement():
    """A quote can exist in the CV and still not cover the requirement.

    The agent claims no coverage, so the quote stays and nothing is rejected.
    """
    uncovered = requirement(0, "backend con Python", name="Experiencia con Kubernetes")

    result = report_for(uncovered).requirements[0]

    assert result.score == 0
    assert result.quote == "backend con Python"
    assert result.quote_status == QuoteStatus.FOUND


def test_a_rejected_quote_keeps_what_the_agent_claimed():
    """A claim of coverage with a quote not in the CV is rejected.

    The rejection keeps the original quote and score, so it can be reviewed later.
    """
    claimed = requirement(1.0, "Kubernetes en producción", name="Experiencia con Kubernetes")

    report = report_for(claimed)

    assert len(report.rejected_quotes) == 1
    rejected = report.rejected_quotes[0]
    assert rejected.requirement == "Experiencia con Kubernetes"
    assert rejected.quote == "Kubernetes en producción"
    assert rejected.original_score == 1.0
    assert rejected.quote_status == QuoteStatus.NOT_FOUND


def test_valid_quotes_are_not_rejected():
    assert report_for(requirement(1.0, "backend con Python")).rejected_quotes == []


def test_score_zero_is_not_a_rejection_even_with_an_invented_quote():
    assert report_for(requirement(0, "Kubernetes en producción")).rejected_quotes == []


def test_summary_counts_after_applying_the_rules():
    report = report_for(
        requirement(1.0, "backend con Python", "Python"),
        requirement(0.4, "Django", "Frameworks"),
        requirement(0.7, "Kubernetes en producción", "Kubernetes"),
        requirement(0, None, "Go"),
    )

    assert report.summary.total == 4
    assert report.summary.covered == 2
    assert report.summary.gaps == 2
