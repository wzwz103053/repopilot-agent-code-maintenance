import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from repopilot_agent.agent import graph

def main() -> None:
    print("=" * 80)
    print("RepoPilot Final Demo: Auto Approve")
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
        "auto_approve": True,
    }

    config = {
        "configurable": {
            "thread_id": "example-final-auto-approve",
        }
    }

    latest_state: dict = {}

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

            if isinstance(update, dict):
                latest_state.update(update)

    print("\n" + "=" * 80)
    print("Final Summary")
    print("=" * 80)

    print("Patch status:", latest_state.get("patch_status"))
    print("Test status:", latest_state.get("test_status"))
    print("PR title:", latest_state.get("pr_title"))
    print()
    print(latest_state.get("final_summary"))


if __name__ == "__main__":
    main()
