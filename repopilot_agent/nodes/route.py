import os

from typing_extensions import Literal

from repopilot_agent.state import RepoPilotState


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def route_after_preflight_guardrails(
    state: RepoPilotState,
) -> Literal["scan_repo", "pr_summary"]:
    """
    Stop early if preflight guardrails block the request.
    """
    status = state.get("guardrail_status", "passed")

    if status == "blocked":
        return "pr_summary"

    return "scan_repo"


def route_after_issue_router(
    state: RepoPilotState,
) -> Literal["retrieval_subgraph", "docs_update_subgraph", "pr_summary"]:
    """
    Route after V15/V16 issue classification.

    V15:
    - bug_fix -> retrieval_subgraph
    - others -> pr_summary

    V16:
    - docs_update -> docs_update_subgraph
    """
    issue_route = state.get("issue_route", "bug_fix")
    supported = state.get("issue_route_supported", issue_route == "bug_fix")

    if not supported:
        return "pr_summary"

    if issue_route == "bug_fix":
        return "retrieval_subgraph"

    if issue_route == "docs_update":
        return "docs_update_subgraph"

    return "pr_summary"


def route_after_patch_safety_guardrails(
    state: RepoPilotState,
) -> Literal["human_review", "pr_summary"]:
    """
    Continue to human review only when:
    - patch validation passed
    - patch evaluation accepted
    - patch safety guardrails passed
    """
    patch_validation_status = state.get("patch_validation_status", "invalid")
    patch_evaluation_status = state.get("patch_evaluation_status", "accepted")
    patch_safety_status = state.get("patch_safety_status", "passed")

    if (
        patch_validation_status == "valid"
        and patch_evaluation_status == "accepted"
        and patch_safety_status == "passed"
    ):
        return "human_review"

    return "pr_summary"


def route_after_patch_validation(
    state: RepoPilotState,
) -> Literal["human_review", "pr_summary"]:
    """
    Backward-compatible route.

    V11+ uses route_after_patch_safety_guardrails instead.
    """
    status = state.get("patch_validation_status", "invalid")

    if status == "valid":
        return "human_review"

    return "pr_summary"


def route_after_human_review(
    state: RepoPilotState,
) -> Literal["apply_patch", "pr_summary"]:
    """
    Apply patch only when approved.
    """
    review_status = state.get("review_status", "unknown")

    if review_status == "approved":
        return "apply_patch"

    return "pr_summary"


def route_after_tests(
    state: RepoPilotState,
) -> Literal["repair_subgraph", "pr_summary"]:
    """
    Route after validation tests.

    passed -> pr_summary
    failed and attempts left -> repair_subgraph
    failed and attempts exhausted -> pr_summary
    """
    test_status = state.get("test_status", "unknown")
    repair_attempts = state.get("repair_attempts", 0)
    max_repair_attempts = state.get(
        "max_repair_attempts",
        _env_int(
            "REPOPILOT_MAX_REPAIR_ATTEMPTS",
            _env_int("REPOPILOT_DEFAULT_MAX_REPAIR_ATTEMPTS", 2),
        ),
    )

    if test_status == "passed":
        return "pr_summary"

    if repair_attempts < max_repair_attempts:
        return "repair_subgraph"

    return "pr_summary"
