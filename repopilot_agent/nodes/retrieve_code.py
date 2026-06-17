from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.search_tools import (
    retrieve_relevant_files,
    format_retrieval_summary,
)


def retrieve_code_node(state: RepoPilotState) -> dict:
    repo_path = state["repo_path"]
    files = state.get("code_files", [])
    keywords = state.get("issue_keywords", [])
    issue_type = state.get("issue_type", "unknown")

    retrieved_files = retrieve_relevant_files(
        repo_path=repo_path,
        files=files,
        keywords=keywords,
        issue_type=issue_type,
        top_k=5,
    )

    relevant_files = [item["path"] for item in retrieved_files]
    retrieval_summary = format_retrieval_summary(retrieved_files)

    return {
        "retrieved_files": retrieved_files,
        "relevant_files": relevant_files,
        "retrieval_summary": retrieval_summary,
    }