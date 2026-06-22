from pathlib import Path


def test_v18_required_project_files_exist():
    required_files = [
        "README.md",
        "langgraph.json",
        ".env.example",
        "repopilot_agent/agent.py",
        "repopilot_agent/state.py",
        "repopilot_agent/agents/patch_evaluator_agent.py",
        "repopilot_agent/nodes/issue_router.py",
        "repopilot_agent/nodes/docs_update.py",
        "repopilot_agent/nodes/patch_evaluator.py",
        "repopilot_agent/subgraphs/retrieval_graph.py",
        "repopilot_agent/subgraphs/docs_update_graph.py",
        "repopilot_agent/subgraphs/patch_graph.py",
        "docs/ARCHITECTURE.md",
        "docs/ARCHITECTURE_CN.md",
        "docs/BENCHMARKING.md",
        "docs/BENCHMARKING_CN.md",
        "docs/DESIGN_DECISIONS.md",
        "docs/DESIGN_DECISIONS_CN.md",
        "docs/RELEASE_READINESS.md",
        "docs/RELEASE_READINESS_CN.md",
        "docs/TEST_MIGRATION.md",
        "docs/TEST_MIGRATION_CN.md",
        "docs/workflow.md",
        "docs/interview_guide.md",
        "docs/resume_description.md",
        "README_CN.md",
        "examples/demos/final_auto_approve_demo.py",
        "examples/demos/final_docs_update_demo.py",
        "examples/demos/final_human_review_demo.py",
        "examples/reset_demo_bug_project.py",
        "examples/run_benchmark.py",
    ]

    for file in required_files:
        assert Path(file).exists(), f"Missing required final release file: {file}"


def test_v18_graph_imports():
    import pytest

    pytest.importorskip(
        "langgraph",
        reason="Graph import smoke test requires optional LangGraph dependency.",
    )
    pytest.importorskip(
        "langchain",
        reason="Graph import smoke test requires optional LangChain dependency.",
    )

    from repopilot_agent.agent import graph

    assert graph is not None
    assert hasattr(graph, "invoke")
    assert hasattr(graph, "stream")


def test_v18_documentation_mentions_key_features():
    architecture = Path("docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    workflow = Path("docs/workflow.md").read_text(encoding="utf-8")
    resume = Path("docs/resume_description.md").read_text(encoding="utf-8")

    required_terms = [
        "LangGraph",
        "LangChain",
        "Issue Router",
        "Patch Evaluator",
        "Guardrails",
        "Human Review",
    ]

    combined = "\n".join([architecture, workflow, resume])

    for term in required_terms:
        assert term in combined
