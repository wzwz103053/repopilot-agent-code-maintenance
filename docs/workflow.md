# RepoPilot Workflow

RepoPilot combines deterministic workflow control with dynamic agent behavior.

## Hybrid Workflow-Agent Design

RepoPilot uses LangGraph for workflow control and LangChain for agent reasoning.

```text
LangGraph Workflow:
- controls order
- controls branching
- controls shared state
- controls safety checks
- controls human review
- controls validation and repair loops

LangChain Agents:
- inspect code
- call repository tools
- reason about root cause
- generate patch plans
- write patches
- evaluate patches
- summarize results