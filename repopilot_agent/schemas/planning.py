from typing import Literal

from pydantic import BaseModel, Field


class PatchPlan(BaseModel):
    """
    Planning Agent 的输出。

    它根据 Repo Navigator Agent 的调查结果，生成最小修改计划。
    """

    files_to_modify: list[str] = Field(
        description=(
            "The minimal set of files that must be modified to fix the issue. "
            "Do not include files that are only useful for understanding or verification."
        )
    )

    plan_steps: list[str] = Field(
        description=(
            "Concrete minimal steps to fix the issue safely. "
            "Do not include optional or speculative changes."
        )
    )

    risk_level: Literal["low", "medium", "high"] = Field(
        description="Risk level of the proposed change."
    )

    safety_notes: list[str] = Field(
        description=(
            "Important safety constraints, edge cases, or things that must not be changed."
        )
    )

    reasoning_summary: str = Field(
        description=(
            "Explain why these files are the minimal files to modify."
        )
    )