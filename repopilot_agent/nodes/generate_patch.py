from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.patch_tools import generate_patch_from_plan


def generate_patch_node(state: RepoPilotState) -> dict:
    print("[graph node] generate_patch")
    repo_path = state["repo_path"]
    issue = state["issue"]
    files_to_modify = state.get("files_to_modify", [])
    plan = state.get("plan", "")

    patch_result = generate_patch_from_plan(
        repo_path=repo_path,
        issue=issue,
        files_to_modify=files_to_modify,
        plan=plan,
    )

    return {
        "patch": patch_result["patch"],
        "patch_status": patch_result["patch_status"],
        "modified_files": patch_result["modified_files"],
    }