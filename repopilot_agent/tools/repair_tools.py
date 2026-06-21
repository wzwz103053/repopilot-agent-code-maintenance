from __future__ import annotations


def repair_from_failure(repo_path: str, failure_type: str, issue: str) -> dict:
    """Compatibility helper for the historical repair_patch node."""
    return {
        "repair_status": "skipped",
        "repair_patch": "",
        "modified_files": [],
        "repair_notes": [
            "Legacy deterministic repair helper did not generate a patch.",
            f"failure_type={failure_type}",
            f"issue={issue}",
        ],
    }
