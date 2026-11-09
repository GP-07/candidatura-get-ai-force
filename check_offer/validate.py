from pydantic import ValidationError

from check_offer.exceptions import ContractError
from check_offer.models import Analysis


def parse_analysis(raw):
    try:
        return Analysis.model_validate_json(raw).requirements
    except ValidationError as error:
        raise ContractError(str(error)) from error
