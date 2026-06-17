from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from repopilot_agent.agent import graph


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def reset_demo_repo() -> None:
    subprocess.run(
        [sys.executable, "tests/reset_demo_bug_project.py"],
        check=True,
    )


def main() -> None:
    print_section("RepoPilot Final Demo: Bug Fix Auto Approve")

    reset_demo_repo()

    repo_path = Path("playground_repo/demo_bug_project").resolve()

    inputs = {
        "repo_path": str(repo_path),
        "issue": "Profile page crashes when user id does not exist.",
        "max_repair_attempts": 2,
        "max_patch_revision_attempts": 1,
        "auto_approve": True,
    }

    config = {
        "configurable": {
            "thread_id": "repopilot-final-bug-fix-demo",
        }
    }

    result = graph.invoke(inputs, config=config)

    print_section("Route")
    print(result.get("issue_route"))

    print_section("Retrieval Summary")
    print(result.get("retrieval_summary"))

    print_section("Root Cause")
    print(result.get("root_cause"))

    print_section("Files To Modify")
    for file in result.get("files_to_modify", []):
        print("-", file)

    print_section("Patch Evaluation")
    print("status:", result.get("patch_evaluation_status"))
    print("score:", result.get("patch_evaluation_score"))
    print("feedback:", result.get("patch_evaluation_feedback"))

    print_section("Patch / Test Status")
    print("patch_status:", result.get("patch_status"))
    print("test_status:", result.get("test_status"))

    print_section("Final Summary")
    print(result.get("final_summary"))

    assert result.get("issue_route") == "bug_fix"
    assert result.get("patch_status") == "applied"
    assert result.get("test_status") == "passed"


if __name__ == "__main__":
    main()