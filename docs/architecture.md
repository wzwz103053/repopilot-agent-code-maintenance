# RepoPilot Architecture

RepoPilot is a LangGraph + LangChain based multi-agent code maintenance system.

It uses a hybrid workflow-agent architecture:

- The outer LangGraph workflow controls deterministic execution, safety boundaries, routing, patch approval, validation, and repair loops.
- The inner LangChain agents dynamically inspect repositories, call tools, reason about root causes, generate patch plans, write patches, evaluate patches, and summarize results.

## High-Level Flow

```text
User Issue
↓
Preflight Guardrails
↓
Scan Repository
↓
Issue Router
├── bug_fix
│   ↓
│   Retrieval Subgraph
│   ↓
│   Investigation Subgraph
│   ↓
│   Patch Subgraph
│
├── docs_update
│   ↓
│   Docs Update Subgraph
│   ↓
│   Patch Subgraph
│
└── unsupported route
    ↓
    PR Summary

↓
Patch Safety Guardrails
↓
Human Review
↓
Apply Patch
↓
Validation Subgraph
↓
Repair Subgraph if tests fail
↓
PR Summary