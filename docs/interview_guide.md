# RepoPilot Interview Guide

## One-Minute Explanation

RepoPilot is a LangGraph + LangChain based multi-agent code maintenance system.

It takes a repository path and a user issue, scans the repository, routes the issue type, retrieves relevant code context, investigates the root cause, generates a patch plan, writes a patch, evaluates patch quality, runs Guardrails, asks for Human Review, applies the patch, runs tests, repairs failures if needed, and produces a final PR-style summary.

## Why LangGraph?

RepoPilot needs explicit workflow control, shared state, conditional routing, subgraphs, repair loops, Human Review, streaming updates, and Studio debugging.

## Why LangChain Agents?

LangChain agents are used for dynamic work:

- repository navigation
- code reading
- root cause analysis
- patch planning
- patch generation
- Patch Evaluator review
- repair analysis
- PR summary generation

## Key Design

RepoPilot uses a hybrid architecture:

```text
Outer layer: LangGraph workflow for control and safety.
Inner layer: LangChain agents for reasoning and tool use.