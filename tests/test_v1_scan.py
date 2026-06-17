from pathlib import Path

from repopilot_agent.agent import graph


repo_path = Path("playground_repo/demo_bug_project").resolve()

result = graph.invoke(
    {
        "repo_path": str(repo_path),
        "issue": "Profile page crashes when user id does not exist.",
    }
)

print("Repo summary:")
print(result["repo_summary"])

print("\nFile tree:")
print(result["file_tree"])

print("\nCode files:")
for file in result["code_files"]:
    print("-", file)