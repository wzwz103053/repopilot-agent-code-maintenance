from pathlib import Path

from repopilot_agent.agent import graph


repo_path = Path("playground_repo/demo_bug_project").resolve()

result = graph.invoke(
    {
        "repo_path": str(repo_path),
        "issue": "Profile page crashes when user id does not exist.",
        "max_repair_attempts": 2,
    }
)

print("=" * 80)
print("Issue type:")
print(result.get("issue_type"))

print("\n" + "=" * 80)
print("Root cause:")
print(result.get("root_cause"))

print("\n" + "=" * 80)
print("Relevant files:")
for file in result.get("relevant_files", []):
    print("-", file)

print("\n" + "=" * 80)
print("Files to modify:")
for file in result.get("files_to_modify", []):
    print("-", file)

print("\n" + "=" * 80)
print("Plan:")
print(result.get("plan"))

print("\n" + "=" * 80)
print("Patch status:")
print(result.get("patch_status"))

print("\n" + "=" * 80)
print("Test status:")
print(result.get("test_status"))

print("\n" + "=" * 80)
print("Final summary:")
print(result.get("final_summary"))