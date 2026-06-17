from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.summary_tools import build_review_summary


def review_node(state: RepoPilotState) -> dict:
    print("[graph node] review")
    summary = build_review_summary(dict(state))

    return {
        "pr_title": summary["pr_title"],
        "pr_summary": summary["pr_summary"],
        "validation_summary": summary["validation_summary"],
        "final_summary": summary["final_summary"],
    }