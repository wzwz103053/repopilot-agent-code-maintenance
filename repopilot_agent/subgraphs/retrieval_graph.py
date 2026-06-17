from langgraph.graph import END, START, StateGraph

from repopilot_agent.nodes.retrieval import (
    build_code_index_node,
    build_retrieval_queries_node,
    retrieve_code_context_node,
)
from repopilot_agent.state import RepoPilotState


builder = StateGraph(RepoPilotState)

builder.add_node("build_code_index", build_code_index_node)
builder.add_node("build_retrieval_queries", build_retrieval_queries_node)
builder.add_node("retrieve_code_context", retrieve_code_context_node)

builder.add_edge(START, "build_code_index")
builder.add_edge("build_code_index", "build_retrieval_queries")
builder.add_edge("build_retrieval_queries", "retrieve_code_context")
builder.add_edge("retrieve_code_context", END)

retrieval_graph = builder.compile()