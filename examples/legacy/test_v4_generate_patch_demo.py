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
print("Patch status:")
print(result["patch_status"])

print("\n" + "=" * 80)
print("Modified files:")
for file in result["modified_files"]:
    print("-", file)

print("\n" + "=" * 80)
print("Patch:")
print(result["patch"])

print("\n" + "=" * 80)
print("Updated app/user_service.py:")
print((repo_path / "app" / "user_service.py").read_text(encoding="utf-8"))