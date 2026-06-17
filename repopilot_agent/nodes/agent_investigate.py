from repopilot_agent.agents.coding_agent import run_coding_investigation
from repopilot_agent.state import RepoPilotState


def agent_investigate_node(state: RepoPilotState) -> dict:
    print("[graph node] agent_investigate")

    repo_path = state["repo_path"]
    issue = state["issue"]
    code_files = state.get("code_files", [])

    result = run_coding_investigation(
        repo_path=repo_path,
        issue=issue,
        code_files=code_files,
    )

    evidence = getattr(result, "evidence", [])

    plan = "\n".join(
        [
            "Root cause:",
            result.root_cause,
            "",
            "Evidence:",
            *[f"- {item}" for item in evidence],
            "",
            "Relevant files:",
            *[f"- {file}" for file in result.relevant_files],
            "",
            "Files to modify:",
            *[f"- {file}" for file in result.files_to_modify],
            "",
            "Plan:",
            *[
                f"{index}. {step}"
                for index, step in enumerate(result.plan_steps, start=1)
            ],
            "",
            "Agent reasoning summary:",
            result.reasoning_summary,
        ]
    )

    return {
        "issue_type": result.issue_type,
        "root_cause": result.root_cause,
        "relevant_files": result.relevant_files,
        "files_to_modify": result.files_to_modify,
        "plan_steps": result.plan_steps,
        "plan": plan,
    }