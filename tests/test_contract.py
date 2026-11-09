import copy
import json

import pytest

from validate import ContractError, parse_analysis


VALID_ANALYSIS = {
    "requirements": [
        {
            "requirement": "Experiencia con Python",
            "score": 1.0,
            "quote": "Backend en Python y Django",
            "justification": "El CV menciona Python de forma directa.",
        },
        {
            "requirement": "Experiencia con Kubernetes",
            "score": 0,
            "quote": None,
            "justification": "El CV no lo menciona.",
        },
    ]
}


def analysis_with_score(score, index=0):
    analysis = copy.deepcopy(VALID_ANALYSIS)
    analysis["requirements"][index]["score"] = score
    return json.dumps(analysis)


def test_parses_a_valid_analysis():
    result = parse_analysis(json.dumps(VALID_ANALYSIS))

    assert len(result) == 2
    assert result[0].requirement == "Experiencia con Python"
    assert result[0].score == 1.0
    assert result[0].quote == "Backend en Python y Django"
    assert result[0].justification == "El CV menciona Python de forma directa."
    assert result[1].quote is None


@pytest.mark.parametrize("score", [1.0, 0.7, 0.4, 0])
def test_accepts_every_rubric_score(score):
    result = parse_analysis(analysis_with_score(score))

    assert result[0].score == score


@pytest.mark.parametrize("score", [0.5, 2, True])
def test_rejects_a_score_outside_the_rubric(score):
    with pytest.raises(ContractError):
        parse_analysis(analysis_with_score(score))


def test_rejects_an_analysis_without_requirements():
    with pytest.raises(ContractError):
        parse_analysis(json.dumps({"requirements": []}))


def test_malformed_json_raises_contract_error():
    with pytest.raises(ContractError):
        parse_analysis("no es json")


def test_error_tells_the_agent_which_item_is_invalid():
    with pytest.raises(ContractError, match=r"requirements\.1\.score"):
        parse_analysis(analysis_with_score(0.5, index=1))
