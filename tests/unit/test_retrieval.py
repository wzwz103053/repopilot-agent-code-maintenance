from pathlib import Path

from repopilot_agent.tools.code_index_tools import (
    build_code_index,
    build_retrieval_queries,
    format_retrieval_context,
    retrieve_code_chunks,
    retrieved_files_from_chunks,
)


def test_v13_build_code_index_for_demo_repo():
    repo_path = Path("playground_repo/demo_bug_project").resolve()

    code_files = [
        "README.md",
        "app/profile.py",
        "app/user_service.py",
        "tests/test_profile.py",
    ]

    chunks = build_code_index(
        repo_path=str(repo_path),
        code_files=code_files,
        chunk_size=40,
        overlap=10,
    )

    assert chunks
    assert any(chunk["file_path"] == "app/user_service.py" for chunk in chunks)
    assert any(chunk["file_path"] == "app/profile.py" for chunk in chunks)


def test_v13_build_retrieval_queries_expands_issue_terms():
    queries = build_retrieval_queries(
        issue="Profile page crashes when user id does not exist."
    )

    joined = " ".join(queries).lower()

    assert "profile" in joined
    assert "user" in joined
    assert "exception" in joined or "error" in joined
    assert "missing" in joined or "unknown" in joined


def test_v13_retrieve_relevant_chunks_for_profile_bug():
    repo_path = Path("playground_repo/demo_bug_project").resolve()

    code_files = [
        "README.md",
        "app/profile.py",
        "app/user_service.py",
        "tests/test_profile.py",
    ]

    chunks = build_code_index(
        repo_path=str(repo_path),
        code_files=code_files,
        chunk_size=40,
        overlap=10,
    )

    queries = build_retrieval_queries(
        issue="Profile page crashes when user id does not exist."
    )

    retrieved = retrieve_code_chunks(
        chunks=chunks,
        queries=queries,
        top_k=5,
    )

    retrieved_files = retrieved_files_from_chunks(retrieved)
    context = format_retrieval_context(retrieved, max_chars=4000)

    assert retrieved
    assert "app/user_service.py" in retrieved_files or "app/profile.py" in retrieved_files
    assert "FILE:" in context
    assert "Retrieved chunk" in context
