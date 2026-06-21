from repopilot_agent.nodes.docs_update import _find_docs_targets
from repopilot_agent.nodes.route import route_after_issue_router


def test_v16_find_readme_target():
    code_files = [
        "app/profile.py",
        "app/user_service.py",
        "README.md",
        "tests/test_profile.py",
    ]

    assert _find_docs_targets(code_files) == ["README.md"]


def test_v16_find_docs_index_target():
    code_files = [
        "app/main.py",
        "docs/index.md",
    ]

    assert _find_docs_targets(code_files) == ["docs/index.md"]


def test_v16_find_any_markdown_target():
    code_files = [
        "app/main.py",
        "CHANGELOG.md",
    ]

    assert _find_docs_targets(code_files) == ["CHANGELOG.md"]


def test_v16_route_docs_update_to_docs_subgraph():
    next_node = route_after_issue_router(
        {
            "issue_route": "docs_update",
            "issue_route_supported": True,
        }
    )

    assert next_node == "docs_update_subgraph"


def test_v16_route_bug_fix_still_to_retrieval():
    next_node = route_after_issue_router(
        {
            "issue_route": "bug_fix",
            "issue_route_supported": True,
        }
    )

    assert next_node == "retrieval_subgraph"
