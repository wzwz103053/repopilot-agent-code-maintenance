from pathlib import Path

from repopilot_agent.agent import graph


repo_path = Path("playground_repo/demo_bug_project").resolve()

inputs = {
    "repo_path": str(repo_path),
    "issue": "Profile page crashes when user id does not exist.",
    "max_repair_attempts": 2,
}

print("=" * 80)
print("RepoPilot V8.1 Trace Run")
print("=" * 80)

final_state = None

for chunk in graph.stream(inputs, stream_mode="updates"):
    print("\n" + "-" * 80)
    print("[langgraph update]")

    for node_name, update in chunk.items():
        print(f"Node finished: {node_name}")

        if isinstance(update, dict):
            print("Updated keys:")
            for key in update.keys():
                print(f"- {key}")

    final_state = chunk

print("\n" + "=" * 80)
print("Final invoke result")
print("=" * 80)

result = graph.invoke(inputs)

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

print("\nPatch status:")
print(result.get("patch_status"))

print("\nTest status:")
print(result.get("test_status"))

print("\nFinal summary:")
print(result.get("final_summary"))