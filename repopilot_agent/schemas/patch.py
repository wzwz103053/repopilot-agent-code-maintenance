from typing import Literal

from pydantic import BaseModel, Field


class PatchProposal(BaseModel):
    """
    Patch Writer Agent 的输出。

    注意：
    Patch Writer Agent 只负责提出 patch，不直接写文件。
    真正写文件由 apply_patch node / tool 完成。
    """

    diff: str = Field(
        description=(
            "A unified diff patch. It must use paths like "
            "--- a/app/file.py and +++ b/app/file.py."
        )
    )

    modified_files: list[str] = Field(
        description="Files modified by this patch."
    )

    explanation: str = Field(
        description="Explain what the patch changes and why."
    )

    risk_level: Literal["low", "medium", "high"] = Field(
        description="Risk level of applying this patch."
    )

    safety_notes: list[str] = Field(
        description="Safety notes and edge cases for this patch."
    )


class PatchValidationResult(BaseModel):
    status: Literal["valid", "invalid"] = Field(
        description="Whether the patch proposal is valid enough to apply."
    )

    errors: list[str] = Field(
        description="Validation errors. Empty when status is valid."
    )

    warnings: list[str] = Field(
        description="Non-blocking warnings about the patch."
    )