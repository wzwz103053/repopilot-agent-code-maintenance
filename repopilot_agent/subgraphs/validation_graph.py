from langgraph.graph import END, START, StateGraph

from repopilot_agent.nodes.run_tests import run_tests_node
from repopilot_agent.state import RepoPilotState


builder = StateGraph(RepoPilotState)

builder.add_node("run_tests", run_tests_node)

builder.add_edge(START, "run_tests")
builder.add_edge("run_tests", END)

validation_graph = builder.compile()