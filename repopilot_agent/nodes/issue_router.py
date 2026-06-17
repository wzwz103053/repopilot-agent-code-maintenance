from __future__ import annotations

import os

from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.issue_router_tools import classify_issue_route


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _supported_routes() -> set[str]:
    raw = os.getenv("REPOPILOT_SUPPORTED_ISSUE_ROUTES", "bug_fix")

    return {
        item.strip()
        for item in raw.split(",")
        if item.strip()
    }


def issue_router_node(state: RepoPilotState) -> dict:
    """
    Classify the issue and choose which workflow route should handle it.

    V15 supports bug_fix execution.
    Other routes are classified and summarized, but not executed yet.
    """
    print("[graph node] issue_router")

    if not _env_bool("REPOPILOT_ENABLE_ISSUE_ROUTER", True):
        return {
            "issue_route": "bug_fix",
            "issue_route_reason": "Issue router disabled; defaulting to bug_fix.",
            "issue_route_confidence": 1.0,
            "issue_route_supported": True,
            "issue_route_candidates": [],
        }

    result = classify_issue_route(
        issue=state["issue"],
        code_files=state.get("code_files", []),
        repo_summary=state.get("repo_summary", ""),
    )

    supported = result.route in _supported_routes()

    return {
        "issue_route": result.route,
        "issue_route_reason": result.reason,
        "issue_route_confidence": result.confidence,
        "issue_route_supported": supported,
        "issue_route_candidates": [
            candidate.model_dump()
            for candidate in result.candidates
        ],
    }