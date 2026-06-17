import subprocess
import sys
from pathlib import Path

from repopilot_agent.agent import graph


print("=" * 80)
print("Reset demo bug project")
print("=" * 80)

subprocess.run(
    [sys.executable, "tests/reset_demo_bug_project.py"],
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
        "thread_id": "repopilot-final-auto-approve",
    }
}

print("\n" + "=" * 80)
print("RepoPilot Final Auto-Approve Run")
print("=" * 80)

latest_state: dict = {}

for chunk in graph.stream(
    inputs,
    config=config,
    stream_mode="updates",
    subgraphs=True,
):
    print("\n" + "-" * 80)
    print("[langgraph update]")

    if isinstance(chunk, tuple):
        namespace, data = chunk
        print("Namespace:", namespace)
    else:
        data = chunk

    for node_name, update in data.items():
        print(f"Node finished: {node_name}")

        if isinstance(update, dict):
            print("Updated keys:")
            for key in update.keys():
                print(f"- {key}")

            latest_state.update(update)

print("\n" + "=" * 80)
print("Final result from streamed state")
print("=" * 80)

result = latest_state

print("\nIssue type:")
print(result.get("issue_type"))

print("\nRoot cause:")
print(result.get("root_cause"))

print("\nRelevant files:")
for file in result.get("relevant_files", []):
    print("-", file)

print("\nFiles to modify:")
for file in result.get("files_to_modify", []):
    print("-", file)

print("\nPatch validation status:")
print(result.get("patch_validation_status"))

print("\nPatch validation errors:")
for error in result.get("patch_validation_errors", []):
    print("-", error)

print("\nReview status:")
print(result.get("review_status"))

print("\nPatch status:")
print(result.get("patch_status"))

print("\nModified files:")
for file in result.get("modified_files", []):
    print("-", file)

print("\nTest status:")
print(result.get("test_status"))

print("\nRepair attempts:")
print(result.get("repair_attempts", 0))

print("\nPR Title:")
print(result.get("pr_title"))

print("\nFinal summary:")
print(result.get("final_summary"))

assert result.get("patch_validation_status") == "valid"
assert result.get("review_status") == "approved"
assert result.get("patch_status") in {"applied", "already_applied"}
assert result.get("test_status") == "passed"
assert "app/user_service.py" in result.get("modified_files", [])