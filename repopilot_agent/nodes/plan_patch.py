from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.plan_tools import build_patch_plan


def plan_patch_node(state: RepoPilotState) -> dict:
    issue = state["issue"]
    retrieved_files = state.get("retrieved_files", [])

    patch_plan = build_patch_plan(
        issue=issue,
        retrieved_files=retrieved_files,
    )

    return {
        "root_cause": patch_plan["root_cause"],
        "files_to_modify": patch_plan["files_to_modify"],
        "plan_steps": patch_plan["plan_steps"],
        "plan": patch_plan["plan"],
    }