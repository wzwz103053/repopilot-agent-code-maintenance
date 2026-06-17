from __future__ import annotations

import os

from repopilot_agent.agents.patch_evaluator_agent import run_patch_evaluation
from repopilot_agent.state import RepoPilotState


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def patch_evaluator_node(state: RepoPilotState) -> dict:
    """
    Evaluate patch quality before patch safety guardrails and human review.
    """
    print("[subgraph node] patch_evaluator_agent")

    max_patch_revision_attempts = state.get(
        "max_patch_revision_attempts",
        _env_int("REPOPILOT_MAX_PATCH_REVISION_ATTEMPTS", 1),
    )

    patch_validation_errors = state.get("patch_validation_errors", [])

    if isinstance(patch_validation_errors, str):
        patch_validation_errors = [patch_validation_errors]

    result = run_patch_evaluation(
        issue_route=state.get("issue_route", state.get("issue_type", "bug_fix")),
        issue=state.get("issue", ""),
        root_cause=state.get("root_cause", ""),
        relevant_files=state.get("relevant_files", []),
        files_to_modify=state.get("files_to_modify", []),
        plan_steps=state.get("plan_steps", []),
        patch=state.get("patch_proposal", state.get("patch", "")),
        patch_validation_status=state.get("patch_validation_status", "unknown"),
        patch_validation_errors=patch_validation_errors,
    )

    return {
        "patch_evaluation_status": result.status,
        "patch_evaluation_score": result.score,
        "patch_evaluation_feedback": result.feedback,
        "patch_evaluation_blocking_issues": result.blocking_issues,
        "patch_evaluation_recommendations": result.recommendations,
        "max_patch_revision_attempts": max_patch_revision_attempts,
    }