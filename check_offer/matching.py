from check_offer.models import (
    QuoteStatus,
    RejectedQuote,
    Report,
    Summary,
    ValidatedRequirement,
)
from check_offer.quotes import check_quote


def run_matching(requirements, cv_text, generic_words):
    """Apply the quote rules to the agent's analysis and build the report.

    Special cases:
    - A score above 0 whose quote is not FOUND is lowered to 0 and recorded as a
      rejected quote, with the score the agent claimed.
    - A score of 0 is never a rejection, because the agent claimed no coverage.
      Its quote is kept whatever its status is.
    - A FOUND quote keeps its score. FOUND does not prove that the quote covers
      the requirement; that remains the agent's judgment.
    """
    validated = []
    rejected_quotes = []

    for requirement in requirements:
        quote_status = check_quote(requirement.quote, cv_text, generic_words)
        score = requirement.score

        if score > 0 and quote_status != QuoteStatus.FOUND:
            rejected_quotes.append(
                RejectedQuote(
                    requirement=requirement.requirement,
                    quote=requirement.quote,
                    original_score=score,
                    quote_status=quote_status,
                )
            )
            score = 0

        validated.append(
            ValidatedRequirement(
                requirement=requirement.requirement,
                score=score,
                quote=requirement.quote,
                justification=requirement.justification,
                quote_status=quote_status,
            )
        )

    covered = sum(1 for requirement in validated if requirement.score > 0)
    summary = Summary(
        total=len(validated), covered=covered, gaps=len(validated) - covered
    )
    return Report(
        summary=summary, requirements=validated, rejected_quotes=rejected_quotes
    )
