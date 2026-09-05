from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .taxonomy import SPECIALIZATIONS


class AnalyzeRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1, max_length=12)
    age: int | None = Field(default=None, ge=0, le=120)
    sex: Literal["male", "female", "other"] | None = None

    @field_validator("symptoms")
    @classmethod
    def clean(cls, v: list[str]) -> list[str]:
        # Trim, drop blanks, cap length — this text goes into a prompt,
        # so unbounded input is unbounded cost.
        out = [s.strip()[:400] for s in v if s and s.strip()]
        if not out:
            raise ValueError("symptoms must contain at least one non-empty entry")
        return out


class ModelAnswer(BaseModel):
    """Exactly what we accept back from the model. Anything else is rejected."""
    specialization: str
    confidence: float = Field(ge=0.0, le=1.0)
    severityScore: int = Field(ge=0, le=100)
    matchedSymptoms: list[str] = Field(default_factory=list)
    explanation: str = Field(max_length=600)

    @field_validator("specialization")
    @classmethod
    def known(cls, v: str) -> str:
        # THE important line. An unknown value here means zero doctors found.
        normalised = v.strip().upper().replace(" ", "_")
        if normalised not in SPECIALIZATIONS:
            raise ValueError(f"unknown specialization: {v!r}")
        return normalised


class AnalyzeResponse(BaseModel):
    specialization: str
    emergency: bool
    conditionType: Literal["NORMAL", "EMERGENCY"]
    confidence: float
    severityScore: int
    matchedSymptoms: list[str]
    explanation: str
    source: Literal["red_flag", "model", "fallback"]
    disclaimer: str