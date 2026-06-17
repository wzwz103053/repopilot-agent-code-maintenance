from langgraph.graph import END, START, StateGraph

from repopilot_agent.nodes.docs_update import (
    docs_plan_node,
    docs_target_node,
)
from repopilot_agent.state import RepoPilotState


builder = StateGraph(RepoPilotState)

builder.add_node("docs_target_selector", docs_target_node)
builder.add_node("docs_plan_builder", docs_plan_node)

builder.add_edge(START, "docs_target_selector")
builder.add_edge("docs_target_selector", "docs_plan_builder")
builder.add_edge("docs_plan_builder", END)

docs_update_graph = builder.compile()