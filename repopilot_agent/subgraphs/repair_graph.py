from langgraph.graph import END, START, StateGraph

from repopilot_agent.agents.repair_agent import run_repair_agent
from repopilot_agent.agents.test_analyst_agent import run_test_analysis
from repopilot_agent.nodes.run_tests import run_tests_node
from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.patch_tools import apply_unified_diff, strip_markdown_fences


def test_analyst_node(state: RepoPilotState) -> dict:
    """
    Analyze failed test output with Test Analyst Agent.
    """
    print("[subgraph node] test_analyst_agent")

    result = run_test_analysis(
        repo_path=state["repo_path"],
        issue=state["issue"],
        code_files=state.get("code_files", []),
        test_command=state.get("test_command", ""),
        test_status=state.get("test_status", "unknown"),
        test_exit_code=state.get("test_exit_code"),
        test_output=state.get("test_output", ""),
        patch=state.get("patch", state.get("patch_proposal", "")),
        modified_files=state.get("modified_files", state.get("patch_modified_files", [])),
    )

    return {
        "failure_type": result.failure_type,
        "failure_analysis": result.failure_analysis,
        "failure_evidence": result.failure_evidence,
        "repair_notes": [f"Suggested next action: {result.suggested_next_action}"],
        "patch_modified_files": result.affected_files or state.get("patch_modified_files", []),
    }


def repair_agent_node(state: RepoPilotState) -> dict:
    """
    Generate a repair patch with Repair Agent.
    """
    print("[subgraph node] repair_agent")

    repair_attempts = state.get("repair_attempts", 0) + 1

    result = run_repair_agent(
        repo_path=state["repo_path"],
        issue=state["issue"],
        code_files=state.get("code_files", []),
        previous_patch=state.get("patch", state.get("patch_proposal", "")),
        modified_files=state.get("modified_files", state.get("patch_modified_files", [])),
        failure_type=state.get("failure_type", "unknown"),
        failure_analysis=state.get("failure_analysis", ""),
        failure_evidence=state.get("failure_evidence", []),
        affected_files=state.get("patch_modified_files", []),
        test_output=state.get("test_output", ""),
    )

    diff = strip_markdown_fences(result.diff)

    return {
        "repair_attempts": repair_attempts,
        "repair_status": "proposed",
        "repair_patch": diff,
        "patch_proposal": diff,
        "patch_explanation": result.explanation,
        "patch_modified_files": result.modified_files,
        "patch_risk_level": result.risk_level,
        "safety_notes": result.safety_notes,
    }


def apply_repair_patch_node(state: RepoPilotState) -> dict:
    """
    Apply repair patch.
    """
    print("[subgraph node] apply_repair_patch")

    repair_patch = state.get("repair_patch", "")

    if not repair_patch.strip():
        return {
            "patch_status": "skipped",
            "patch": "",
            "modified_files": [],
            "apply_patch_error": "No repair patch was proposed.",
        }

    return apply_unified_diff(
        repo_path=state["repo_path"],
        diff=repair_patch,
    )


builder = StateGraph(RepoPilotState)

builder.add_node("test_analyst_agent", test_analyst_node)
builder.add_node("repair_agent", repair_agent_node)
builder.add_node("apply_repair_patch", apply_repair_patch_node)
builder.add_node("run_tests", run_tests_node)

builder.add_edge(START, "test_analyst_agent")
builder.add_edge("test_analyst_agent", "repair_agent")
builder.add_edge("repair_agent", "apply_repair_patch")
builder.add_edge("apply_repair_patch", "run_tests")
builder.add_edge("run_tests", END)

repair_graph = builder.compile()