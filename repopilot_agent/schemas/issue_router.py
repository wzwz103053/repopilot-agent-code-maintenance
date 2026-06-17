from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


IssueRoute = Literal[
    "bug_fix",
    "test_generation",
    "refactor",
    "docs_update",
    "security_review",
    "unknown",
]


class IssueRouteCandidate(BaseModel):
    route: IssueRoute
    score: float = Field(description="Heuristic route score.")
    reasons: list[str] = Field(default_factory=list)


class IssueRouteResult(BaseModel):
    route: IssueRoute
    reason: str
    confidence: float
    candidates: list[IssueRouteCandidate]