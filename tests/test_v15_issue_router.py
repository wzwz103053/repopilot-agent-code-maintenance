from pathlib import Path

from repopilot_agent.nodes.route import route_after_issue_router
from repopilot_agent.tools.issue_router_tools import classify_issue_route


def test_v15_route_bug_fix_issue():
    result = classify_issue_route(
        issue="Profile page crashes when user id does not exist.",
        code_files=[
            "app/profile.py",
            "app/user_service.py",
            "tests/test_profile.py",
        ],
        repo_summary="Demo profile project",
    )

    assert result.route == "bug_fix"
    assert result.confidence > 0
    assert result.candidates


def test_v15_route_test_generation_issue():
    result = classify_issue_route(
        issue="Add unit tests for missing user profile behavior.",
        code_files=[
            "app/profile.py",
            "app/user_service.py",
            "tests/test_profile.py",
        ],
    )

    assert result.route == "test_generation"


def test_v15_route_docs_update_issue():
    result = classify_issue_route(
        issue="Update README with setup instructions and usage examples.",
        code_files=[
            "README.md",
            "app/profile.py",
        ],
    )

    assert result.route == "docs_update"


def test_v15_route_refactor_issue():
    result = classify_issue_route(
        issue="Refactor user service to simplify profile formatting logic.",
        code_files=[
            "app/user_service.py",
        ],
    )

    assert result.route == "refactor"


def test_v15_route_security_review_issue():
    result = classify_issue_route(
        issue="Review the repository for prompt injection and secret leakage risks.",
        code_files=[
            "app/user_service.py",
        ],
    )

    assert result.route == "security_review"


def test_v15_route_unknown_issue():
    result = classify_issue_route(
        issue="Please take a look at this project.",
        code_files=[
            "app/user_service.py",
        ],
    )

    assert result.route == "unknown"


def test_v15_route_after_issue_router_bug_fix():
    next_node = route_after_issue_router(
        {
            "issue_route": "bug_fix",
            "issue_route_supported": True,
        }
    )

    assert next_node == "retrieval_subgraph"


def test_v15_route_after_issue_router_unsupported():
    next_node = route_after_issue_router(
        {
            "issue_route": "docs_update",
            "issue_route_supported": False,
        }
    )

    assert next_node == "pr_summary"


def test_v15_graph_imports():
    from repopilot_agent.agent import graph

    assert graph is not None
    assert hasattr(graph, "stream")
    assert hasattr(graph, "invoke")