from typing import Literal

from pydantic import BaseModel, Field


class RepoNavigationResult(BaseModel):
    """
    Repo Navigator Agent 的输出。

    它只负责调查代码库：
    - 问题类型
    - 直接根因
    - 相关文件
    - 证据
    - 调查总结

    它不负责决定怎么改。
    """

    issue_type: Literal[
        "bug_fix",
        "feature_request",
        "refactor",
        "test_request",
        "documentation",
        "unknown",
    ] = Field(description="The type of the issue.")

    root_cause: str = Field(
        description=(
            "The most likely direct root cause based only on inspected repository files. "
            "Do not blame caller files if the bug is caused by a lower-level function."
        )
    )

    relevant_files: list[str] = Field(
        description=(
            "Files relevant for understanding the issue. "
            "This may include source files, callers, tests, and documentation."
        )
    )

    evidence: list[str] = Field(
        description=(
            "Short evidence items from inspected files that support the root cause. "
            "Each item should mention the file path and observed code behavior."
        )
    )

    reasoning_summary: str = Field(
        description=(
            "Short explanation of how the inspected files support the root cause."
        )
    )


class InvestigationResult(BaseModel):
    """
    兼容旧 V8 的完整 investigation 输出。
    后续如果旧代码还引用 InvestigationResult，不会立刻坏。
    """

    issue_type: Literal[
        "bug_fix",
        "feature_request",
        "refactor",
        "test_request",
        "documentation",
        "unknown",
    ]

    root_cause: str
    relevant_files: list[str]
    files_to_modify: list[str]
    plan_steps: list[str]
    risk_level: Literal["low", "medium", "high"]
    evidence: list[str] = []
    reasoning_summary: str