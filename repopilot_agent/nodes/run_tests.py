from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.test_tools import run_test_command


def run_tests_node(state: RepoPilotState) -> dict:
    print("[graph node] run_tests")
    repo_path = state["repo_path"]

    result = run_test_command(repo_path)

    return {
        "test_command": result["test_command"],
        "test_status": result["test_status"],
        "test_exit_code": result["test_exit_code"],
        "test_output": result["test_output"],
    }