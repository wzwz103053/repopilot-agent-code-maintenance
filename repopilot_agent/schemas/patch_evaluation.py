from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PatchEvaluationResult(BaseModel):
    status: Literal["accepted", "rejected"] = Field(
        description="Whether the patch is good enough to continue."
    )

    score: float = Field(
        description="Quality score from 0.0 to 1.0."
    )

    feedback: str = Field(
        description="Human-readable evaluation feedback."
    )

    blocking_issues: list[str] = Field(
        default_factory=list,
        description="Issues that block the patch from continuing.",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Concrete recommendations for revising the patch.",
    )