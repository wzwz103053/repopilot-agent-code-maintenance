from __future__ import annotations


def build_review_summary(state: dict) -> dict:
    """Build a deterministic PR-style summary for the legacy review node."""
    issue = state.get("issue", "")
    test_status = state.get("test_status", "not_run")
    modified_files = state.get("modified_files", [])

    return {
        "pr_title": "RepoPilot maintenance summary",
        "pr_summary": f"Handled issue: {issue}",
        "validation_summary": f"Test status: {test_status}",
        "final_summary": (
            f"Issue: {issue}\n"
            f"Modified files: {', '.join(modified_files) or 'none'}\n"
            f"Validation: {test_status}"
        ),
    }
