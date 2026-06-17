from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.patch_tools import apply_unified_diff


def apply_patch_node(state: RepoPilotState) -> dict:
    """
    Apply the patch proposal after human review approval.
    """
    print("[graph node] apply_patch")

    review_status = state.get("review_status", "unknown")

    if review_status != "approved":
        return {
            "patch_status": "skipped",
            "patch": state.get("patch_proposal", ""),
            "modified_files": [],
            "apply_patch_error": (
                f"Patch was not applied because review_status={review_status}."
            ),
        }

    repo_path = state["repo_path"]
    patch = state.get("patch_proposal", "")

    if not patch.strip():
        return {
            "patch_status": "skipped",
            "patch": "",
            "modified_files": [],
            "apply_patch_error": "No patch proposal found.",
        }

    return apply_unified_diff(repo_path=repo_path, diff=patch)