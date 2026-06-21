from pathlib import Path

from repopilot_agent.agent import graph


repo_path = Path("playground_repo/demo_bug_project").resolve()

inputs = {
    "repo_path": str(repo_path),
    "issue": "Profile page crashes when user id does not exist.",
    "max_repair_attempts": 2,
}

print("=" * 80)
print("RepoPilot V9 Multi-Agent Run")
print("=" * 80)

print("\n" + "=" * 80)
print("Streaming updates")
print("=" * 80)

latest_state: dict = {}

for chunk in graph.stream(
    inputs,
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

            # 关键：把每次节点更新合并到 latest_state
            # 这样后面就不需要再 graph.invoke 跑第二遍了
            latest_state.update(update)

print("\n" + "=" * 80)
print("Final result from streamed state")
print("=" * 80)

result = latest_state

print("\nIssue type:")
print(result.get("issue_type"))

print("\nRoot cause:")
print(result.get("root_cause"))

print("\nEvidence:")
for item in result.get("evidence", []):
    print("-", item)

print("\nRelevant files:")
for file in result.get("relevant_files", []):
    print("-", file)

print("\nFiles to modify:")
for file in result.get("files_to_modify", []):
    print("-", file)

print("\nRisk level:")
print(result.get("risk_level"))

print("\nSafety notes:")
for note in result.get("safety_notes", []):
    print("-", note)

print("\nPlan:")
print(result.get("plan"))

print("\nPatch status:")
print(result.get("patch_status"))

print("\nTest status:")
print(result.get("test_status"))

print("\nFinal summary:")
print(result.get("final_summary"))