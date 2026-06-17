from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.repair_tools import repair_from_failure


def merge_unique(left: list[str], right: list[str]) -> list[str]:
    result: list[str] = []
    seen = set()

    for item in left + right:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def repair_patch_node(state: RepoPilotState) -> dict:
    repo_path = state["repo_path"]
    issue = state["issue"]
    failure_type = state.get("failure_type", "unknown")

    repair_attempts = state.get("repair_attempts", 0) + 1

    repair_result = repair_from_failure(
        repo_path=repo_path,
        failure_type=failure_type,
        issue=issue,
    )

    existing_modified_files = state.get("modified_files", [])
    repair_modified_files = repair_result["modified_files"]

    combined_modified_files = merge_unique(
        existing_modified_files,
        repair_modified_files,
    )

    previous_patch = state.get("patch", "")
    repair_patch = repair_result["repair_patch"]

    if previous_patch and repair_patch:
        combined_patch = previous_patch + "\n\n# Repair patch\n" + repair_patch
    else:
        combined_patch = previous_patch or repair_patch

    return {
        "repair_attempts": repair_attempts,
        "repair_status": repair_result["repair_status"],
        "repair_patch": repair_patch,
        "modified_files": combined_modified_files,
        "patch": combined_patch,
    }