from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from repopilot_agent.nodes.apply_patch import apply_patch_node
from repopilot_agent.nodes.guardrails import (
    patch_safety_guardrails_node,
    preflight_guardrails_node,
)
from repopilot_agent.nodes.human_review import human_review_node
from repopilot_agent.nodes.issue_router import issue_router_node
from repopilot_agent.nodes.pr_summary import pr_summary_node
from repopilot_agent.nodes.route import (
    route_after_human_review,
    route_after_issue_router,
    route_after_patch_safety_guardrails,
    route_after_preflight_guardrails,
    route_after_tests,
)
from repopilot_agent.nodes.scan_repo import scan_repo_node
from repopilot_agent.state import RepoPilotState
from repopilot_agent.subgraphs.docs_update_graph import docs_update_graph
from repopilot_agent.subgraphs.investigation_graph import investigation_graph
from repopilot_agent.subgraphs.patch_graph import patch_graph
from repopilot_agent.subgraphs.repair_graph import repair_graph
from repopilot_agent.subgraphs.retrieval_graph import retrieval_graph
from repopilot_agent.subgraphs.validation_graph import validation_graph


builder = StateGraph(RepoPilotState)

builder.add_node("preflight_guardrails", preflight_guardrails_node)
builder.add_node("scan_repo", scan_repo_node)
builder.add_node("issue_router", issue_router_node)

builder.add_node("retrieval_subgraph", retrieval_graph)
builder.add_node("docs_update_subgraph", docs_update_graph)
builder.add_node("investigation_subgraph", investigation_graph)
builder.add_node("patch_subgraph", patch_graph)

builder.add_node("patch_safety_guardrails", patch_safety_guardrails_node)
builder.add_node("human_review", human_review_node)
builder.add_node("apply_patch", apply_patch_node)
builder.add_node("validation_subgraph", validation_graph)
builder.add_node("repair_subgraph", repair_graph)
builder.add_node("pr_summary", pr_summary_node)

builder.add_edge(START, "preflight_guardrails")

builder.add_conditional_edges(
    "preflight_guardrails",
    route_after_preflight_guardrails,
)

builder.add_edge("scan_repo", "issue_router")

builder.add_conditional_edges(
    "issue_router",
    route_after_issue_router,
)

# bug_fix route
builder.add_edge("retrieval_subgraph", "investigation_subgraph")
builder.add_edge("investigation_subgraph", "patch_subgraph")

# docs_update route
builder.add_edge("docs_update_subgraph", "patch_subgraph")

# shared patch/review/validation route
builder.add_edge("patch_subgraph", "patch_safety_guardrails")

builder.add_conditional_edges(
    "patch_safety_guardrails",
    route_after_patch_safety_guardrails,
)

builder.add_conditional_edges(
    "human_review",
    route_after_human_review,
)

builder.add_edge("apply_patch", "validation_subgraph")

builder.add_conditional_edges(
    "validation_subgraph",
    route_after_tests,
)

builder.add_conditional_edges(
    "repair_subgraph",
    route_after_tests,
)

builder.add_edge("pr_summary", END)

checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)