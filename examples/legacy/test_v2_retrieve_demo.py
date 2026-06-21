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
print("Repo summary:")
print(result["repo_summary"])

print("\n" + "=" * 80)
print("Issue analysis:")
print("Issue type:", result["issue_type"])
print("Issue keywords:", result["issue_keywords"])
print("Issue summary:", result["issue_summary"])

print("\n" + "=" * 80)
print("Retrieval summary:")
print(result["retrieval_summary"])

print("\n" + "=" * 80)
print("Relevant files:")
for file in result["relevant_files"]:
    print("-", file)

print("\n" + "=" * 80)
print("Retrieved snippets:")
for item in result["retrieved_files"]:
    print("\n" + "#" * 80)
    print(f"FILE: {item['path']}")
    print(f"SCORE: {item['score']}")
    print("REASONS:")
    for reason in item["reasons"]:
        print("-", reason)

    print("\nSNIPPET:")
    print(item["snippet"])