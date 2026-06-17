from typing import Literal

from pydantic import BaseModel, Field


class PRSummary(BaseModel):
    """
    PR Summary Agent 的输出。
    """

    title: str = Field(description="Short PR title.")

    summary: str = Field(
        description="Concise summary of the change."
    )

    root_cause: str = Field(
        description="Root cause of the issue."
    )

    changed_files: list[str] = Field(
        description="Files changed by the patch."
    )

    validation: str = Field(
        description="How the change was validated."
    )

    risk_level: Literal["low", "medium", "high"] = Field(
        description="Risk level of the final change."
    )

    reviewer_checklist: list[str] = Field(
        description="Checklist for human reviewers."
    )

    final_summary: str = Field(
        description="Full final report combining issue, fix, validation, and risks."
    )