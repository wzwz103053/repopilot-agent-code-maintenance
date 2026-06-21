def test_graph_imports_without_running_llm():
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
