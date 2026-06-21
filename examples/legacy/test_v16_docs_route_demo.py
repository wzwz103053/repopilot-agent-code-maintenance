from pathlib import Path

from repopilot_agent.agent import graph


repo_path = Path("playground_repo/demo_bug_project").resolve()

inputs = {
    "repo_path": str(repo_path),
    "issue": "Update README with setup instructions and usage examples.",
    "max_repair_attempts": 2,
    "auto_approve": True,
}

config = {
    "configurable": {
        "thread_id": "repopilot-v16-docs-route-demo",
    }
}

result = graph.invoke(inputs, config=config)

print("=" * 80)
print("V16 Docs Update Route Demo")
print("=" * 80)

print("Issue route:")
print(result.get("issue_route"))

print("\nDocs target files:")
print(result.get("docs_target_files"))

print("\nFiles to modify:")
print(result.get("files_to_modify"))

print("\nPatch status:")
print(result.get("patch_status"))

print("\nTest status:")
print(result.get("test_status"))

print("\nFinal summary:")
print(result.get("final_summary"))

assert result.get("issue_route") == "docs_update"
assert result.get("issue_route_supported") is True
assert result.get("docs_target_files")
assert result.get("files_to_modify") == result.get("docs_target_files")