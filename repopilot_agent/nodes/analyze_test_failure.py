from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.failure_tools import analyze_failure_output


def analyze_test_failure_node(state: RepoPilotState) -> dict:
    test_output = state.get("test_output", "")
    test_exit_code = state.get("test_exit_code")

    analysis = analyze_failure_output(
        test_output=test_output,
        test_exit_code=test_exit_code,
    )

    return {
        "failure_type": analysis["failure_type"],
        "failure_analysis": analysis["failure_analysis"],
    }