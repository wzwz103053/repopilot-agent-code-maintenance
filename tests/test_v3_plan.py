from pathlib import Path

from repopilot_agent.agent import graph


repo_path = Path("playground_repo/demo_bug_project").resolve()

result = graph.invoke(
    {
        "repo_path": str(repo_path),
        "issue": "Profile page crashes when user id does not exist.",
    }
)

print("=" * 80)
print("Issue:")
print(result["issue"])

print("\n" + "=" * 80)
print("Issue analysis:")
print("Issue type:", result["issue_type"])
print("Keywords:", result["issue_keywords"])

print("\n" + "=" * 80)
print("Relevant files:")
for file in result["relevant_files"]:
    print("-", file)

print("\n" + "=" * 80)
print("Files to modify:")
for file in result["files_to_modify"]:
    print("-", file)

print("\n" + "=" * 80)
print("Root cause:")
print(result["root_cause"])

print("\n" + "=" * 80)
print("Plan:")
print(result["plan"])