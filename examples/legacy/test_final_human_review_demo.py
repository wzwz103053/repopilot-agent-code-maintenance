import subprocess
import sys
from pathlib import Path

from langgraph.types import Command

from repopilot_agent.agent import graph


print("=" * 80)
print("Reset demo bug project")
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
        "thread_id": "repopilot-final-human-review",
    }
}


def print_chunk(chunk, latest_state: dict) -> bool:
    """
    打印 LangGraph updates。
    返回值：
    - True: 发现 interrupt
    - False: 没有 interrupt
    """
    print("\n" + "-" * 80)
    print("[langgraph update]")

    if isinstance(chunk, tuple):
        namespace, data = chunk
        print("Namespace:", namespace)
    else:
        data = chunk

    interrupt_found = False

    for node_name, update in data.items():
        print(f"Node finished: {node_name}")

        if node_name == "__interrupt__":
            interrupt_found = True
            print("Interrupt payload:")
            print(update)
            continue

        if isinstance(update, dict):
            print("Updated keys:")
            for key in update.keys():
                print(f"- {key}")

            latest_state.update(update)

    return interrupt_found


print("\n" + "=" * 80)
print("RepoPilot Final Human Review Run: before interrupt")
print("=" * 80)

latest_state: dict = {}
interrupted = False

for chunk in graph.stream(
    inputs,
    config=config,
    stream_mode="updates",
    subgraphs=True,
):
    if print_chunk(chunk, latest_state):
        interrupted = True
        break

assert interrupted, "Expected human_review interrupt, but no interrupt occurred."

print("\n" + "=" * 80)
print("Resume from human review interrupt")
print("=" * 80)

resume_command = Command(
    resume={
        "decision": "approve",
        "comment": "Patch reviewed and approved in test_final_human_review.py.",
    }
)

for chunk in graph.stream(
    resume_command,
    config=config,
    stream_mode="updates",
    subgraphs=True,
):
    print_chunk(chunk, latest_state)

print("\n" + "=" * 80)
print("Final result from streamed state")
print("=" * 80)

result = latest_state

print("\nReview status:")
print(result.get("review_status"))

print("\nHuman review decision:")
print(result.get("human_review_decision"))

print("\nHuman review comment:")
print(result.get("human_review_comment"))

print("\nPatch status:")
print(result.get("patch_status"))

print("\nTest status:")
print(result.get("test_status"))

print("\nPR Title:")
print(result.get("pr_title"))

print("\nFinal summary:")
print(result.get("final_summary"))

assert result.get("review_status") == "approved"
assert result.get("human_review_decision") == "approve"
assert result.get("patch_status") in {"applied", "already_applied"}
assert result.get("test_status") == "passed"
assert result.get("pr_title")
