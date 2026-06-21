from __future__ import annotations


def build_patch_plan(issue: str, retrieved_files: list[str]) -> dict:
    """Compatibility helper for the historical plan_patch node."""
    files_to_modify = [
        file
        for file in retrieved_files
        if file.endswith(".py") and not file.startswith("tests/")
    ]

    if not files_to_modify and retrieved_files:
        files_to_modify = [retrieved_files[0]]

    root_cause = (
        "The issue requires inspection of the retrieved files. "
        "Use the smallest direct root-cause change."
    )

    plan_steps = [
        "Inspect the retrieved files and identify the direct root cause.",
        "Modify only the minimal file set needed for the issue.",
        "Run the repository tests after applying the patch.",
    ]

    return {
        "root_cause": root_cause,
        "files_to_modify": files_to_modify,
        "plan_steps": plan_steps,
        "plan": "\n".join(plan_steps),
    }
