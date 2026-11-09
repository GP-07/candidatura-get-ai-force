from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


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
