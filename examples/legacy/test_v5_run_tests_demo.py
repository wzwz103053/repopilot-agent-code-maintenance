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
print("Test command:")
print(result["test_command"])

print("\n" + "=" * 80)
print("Test status:")
print(result["test_status"])

print("\n" + "=" * 80)
print("Test exit code:")
print(result["test_exit_code"])

print("\n" + "=" * 80)
print("Test output:")
print(result["test_output"])