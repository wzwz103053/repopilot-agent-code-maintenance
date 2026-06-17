from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.search_tools import analyze_issue_text


def analyze_issue_node(state: RepoPilotState) -> dict:
    issue = state["issue"]

    analysis = analyze_issue_text(issue)

    return {
        "issue_type": analysis["issue_type"],
        "issue_keywords": analysis["issue_keywords"],
        "issue_summary": analysis["issue_summary"],
    }