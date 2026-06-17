from typing import Literal

from pydantic import BaseModel, Field


class GuardrailFinding(BaseModel):
    """
    A single guardrail finding.

    level:
    - info: informative only
    - warning: suspicious but not blocked
    - block: must stop execution
    """

    level: Literal["info", "warning", "block"] = Field(
        description="Severity level of the finding."
    )

    category: str = Field(
        description="Finding category, e.g. prompt_injection, secret, unsafe_patch."
    )

    message: str = Field(
        description="Human-readable explanation."
    )

    source: str = Field(
        description="Where the issue was found, e.g. issue, repo_path, patch, file path."
    )


class GuardrailResult(BaseModel):
    status: Literal["passed", "blocked"] = Field(
        description="Whether the guardrail check passed or blocked execution."
    )

    findings: list[GuardrailFinding] = Field(
        description="Guardrail findings."
    )

    block_reason: str = Field(
        description="Reason for blocking. Empty when status is passed."
    )