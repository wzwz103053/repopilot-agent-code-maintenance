from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.file_tools import (
    scan_code_files,
    build_file_tree,
    summarize_repo_files,
)


def scan_repo_node(state: RepoPilotState) -> dict:
    print("[graph node] scan_repo")
    repo_path = state["repo_path"]

    files = scan_code_files(repo_path)
    file_tree = build_file_tree(files)
    repo_summary = summarize_repo_files(files)

    return {
        "code_files": files,
        "file_tree": file_tree,
        "repo_summary": repo_summary,
    }
