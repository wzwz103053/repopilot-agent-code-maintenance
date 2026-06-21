import subprocess
import sys
from pathlib import Path

from langgraph.types import Command

from repopilot_agent.agent import graph


def main() -> None:
    print("=" * 80)
    print("RepoPilot Final Demo: Human Review")
    print("=" * 80)

    subprocess.run(
        [sys.executable, "examples/reset_demo_bug_project.py"],
        check=True,
    )

    repo_path = Path("playground_repo/demo_bug_project").resolve()

    inputs = {
        "repo_path": str(repo_path),
        "issue": "Profile page crashes when user id does not exist.",
        "max_repair_attempts": 2,
        "auto_approve": False,
    }

    config = {
        "configurable": {
            "thread_id": "example-final-human-review",
        }
    }

    latest_state: dict = {}
    interrupted = False

    print("\nRunning until human review interrupt...\n")

    for chunk in graph.stream(
        inputs,
        config=config,
        stream_mode="updates",
        subgraphs=True,
    ):
        if isinstance(chunk, tuple):
            namespace, data = chunk
            print("\nNamespace:", namespace)
        else:
            data = chunk

        for node_name, update in data.items():
            print(f"Node finished: {node_name}")

            if node_name == "__interrupt__":
                interrupted = True
                print("\nPatch review interrupt payload:")
                print(update)
                break

            if isinstance(update, dict):
                latest_state.update(update)

        if interrupted:
            break

    if not interrupted:
        raise RuntimeError("Expected human review interrupt, but none occurred.")

    print("\n" + "=" * 80)
    print("Patch Proposal")
    print("=" * 80)
    print(latest_state.get("patch_proposal", ""))

    decision = input("\nApprove patch? [y/N]: ").strip().lower()

    if decision == "y":
        resume_payload = {
            "decision": "approve",
            "comment": "Approved from CLI demo.",
        }
    else:
        resume_payload = {
            "decision": "reject",
            "comment": "Rejected from CLI demo.",
        }

    print("\nResuming graph...\n")

    for chunk in graph.stream(
        Command(resume=resume_payload),
        config=config,
        stream_mode="updates",
        subgraphs=True,
    ):
        if isinstance(chunk, tuple):
            namespace, data = chunk
            print("\nNamespace:", namespace)
        else:
            data = chunk

        for node_name, update in data.items():
            print(f"Node finished: {node_name}")

            if isinstance(update, dict):
                latest_state.update(update)

    print("\n" + "=" * 80)
    print("Final Summary")
    print("=" * 80)

    print("Review status:", latest_state.get("review_status"))
    print("Patch status:", latest_state.get("patch_status"))
    print("Test status:", latest_state.get("test_status"))
    print("PR title:", latest_state.get("pr_title"))
    print()
    print(latest_state.get("final_summary"))


if __name__ == "__main__":
    main()
