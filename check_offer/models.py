from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class QuoteStatus(Enum):
    """Result of checking a quote against the CV.

    FOUND only means that the quote exists in the CV and is not a single generic
    word. Whether the quote covers the requirement is decided by the score.
    """

    FOUND = "found"
    EMPTY = "empty"
    NOT_FOUND = "not_found"
    GENERIC_WORD = "generic_word"


class Requirement(BaseModel):
    requirement: NonBlankText
    score: Literal[0, 0.4, 0.7, 1.0]
    quote: str | None
    justification: NonBlankText

    @field_validator("score", mode="before")
    @classmethod
    def reject_booleans(cls, value):
        if isinstance(value, bool):
            raise ValueError("score must be a number, not a boolean")
        return value


class Analysis(BaseModel):
    requirements: list[Requirement] = Field(min_length=1)
