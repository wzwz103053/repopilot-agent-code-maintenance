from typing import Literal

from pydantic import BaseModel, Field


class TestFailureAnalysis(BaseModel):
    """
    Test Analyst Agent 的输出。
    """

    failure_type: Literal[
        "none",
        "import_error",
        "assertion_failure",
        "runtime_error",
        "patch_did_not_apply",
        "wrong_fix",
        "environment_error",
        "unknown",
    ] = Field(description="Classified failure type.")

    failure_analysis: str = Field(
        description="Human-readable explanation of why tests failed."
    )

    failure_evidence: list[str] = Field(
        description="Specific evidence from test output or repository files."
    )

    suggested_next_action: Literal[
        "rerun_tests",
        "repair_patch",
        "ask_human",
        "stop",
    ] = Field(description="Recommended next action after analysis.")

    affected_files: list[str] = Field(
        description="Files likely related to the failure."
    )


class TestRunResult(BaseModel):
    test_command: str
    test_status: Literal["passed", "failed", "error", "unknown"]
    test_exit_code: int | None
    test_output: str