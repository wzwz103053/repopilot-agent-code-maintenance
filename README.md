# RepoPilot

RepoPilot is a LangGraph + LangChain based multi-agent software maintenance system.

It takes a repository issue as input, investigates the codebase, identifies the root cause, creates a minimal patch plan, proposes a unified diff, pauses for human review when required, applies the patch, runs tests, optionally enters a repair loop, and generates a pull request style summary.

## Why this project exists

Modern coding agents should not be simple chatbots. A useful engineering agent needs to:

* inspect repository files through tools
* distinguish evidence from assumptions
* plan minimal code changes
* propose patches instead of blindly modifying files
* support human approval before risky actions
* run validation tests
* use test failures as feedback
* maintain graph state across long-running workflows

RepoPilot demonstrates these capabilities using LangChain agents and LangGraph orchestration.

## Core capabilities

* Multi-agent repository investigation
* Tool-calling based file reading and code search
* Root cause analysis with evidence
* Minimal patch planning
* Patch Writer Agent that generates unified diff proposals
* Patch validation before application
* Human-in-the-loop patch review with LangGraph interrupt
* Checkpoint-based resume using thread_id
* Automatic patch application after approval
* Pytest validation
* Test failure routing into repair workflow
* PR Summary Agent
* Streaming execution trace for main graph and subgraphs

## Architecture

```text
START
  ↓
scan_repo
  ↓
investigation_subgraph
  ├── repo_navigator_agent
  └── planning_agent
  ↓
patch_subgraph
  ├── patch_writer_agent
  └── patch_validator
  ↓
human_review
  ├── approve → apply_patch
  └── reject  → pr_summary
  ↓
validation_subgraph
  └── run_tests
  ↓
route_after_tests
  ├── passed → pr_summary
  └── failed → repair_subgraph
                  ├── test_analyst_agent
                  ├── repair_agent
                  ├── apply_repair_patch
                  └── run_tests
```

## Agents

### Repo Navigator Agent

Reads repository files, searches code, collects evidence, and identifies the direct root cause of the issue.

Tools:

* `list_repo_files`
* `read_repo_file`
* `search_repo_code`

### Planning Agent

Converts investigation results into a minimal safe patch plan.

It separates:

* `relevant_files`: files useful for understanding the issue
* `files_to_modify`: files that actually need code changes

### Patch Writer Agent

Generates a unified diff patch proposal.

It does not directly modify files. Patch application is handled by a separate node after validation and review.

### Test Analyst Agent

Analyzes failed pytest output and classifies the failure.

Example failure types:

* import error
* assertion failure
* runtime error
* wrong fix
* environment error

### Repair Agent

Uses failed test output and failure analysis to propose a repair patch.

### PR Summary Agent

Generates a pull request style final summary including:

* title
* issue summary
* root cause
* changed files
* validation result
* reviewer checklist
* final report

## LangGraph features used

* `StateGraph`
* shared typed state
* nodes
* conditional edges
* subgraphs
* checkpointer
* thread_id based persistence
* interrupt based human review
* streaming updates
* repair loop routing

## LangChain features used

* `create_agent`
* tool calling
* custom tools
* OpenAI-compatible chat model integration
* structured JSON parsing with Pydantic schemas
* multi-agent decomposition

## Project structure

```text
repopilot/
├── repopilot_agent/
│   ├── agent.py
│   ├── state.py
│   ├── config.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── repo_navigator_agent.py
│   │   ├── planning_agent.py
│   │   ├── patch_writer_agent.py
│   │   ├── test_analyst_agent.py
│   │   ├── repair_agent.py
│   │   └── pr_summary_agent.py
│   ├── schemas/
│   │   ├── investigation.py
│   │   ├── planning.py
│   │   ├── patch.py
│   │   ├── testing.py
│   │   └── review.py
│   ├── tools/
│   │   ├── repo_tools.py
│   │   ├── patch_tools.py
│   │   ├── test_tools.py
│   │   └── agent_tools.py
│   ├── nodes/
│   │   ├── scan_repo.py
│   │   ├── human_review.py
│   │   ├── apply_patch.py
│   │   ├── run_tests.py
│   │   ├── pr_summary.py
│   │   └── route.py
│   └── subgraphs/
│       ├── investigation_graph.py
│       ├── patch_graph.py
│       ├── validation_graph.py
│       └── repair_graph.py
├── playground_repo/
│   └── demo_bug_project/
├── tests/
├── examples/
├── README.md
├── pyproject.toml
├── langgraph.json
└── .env.example
```

## Setup

Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies.

```powershell
pip install -e .
pip install langchain langgraph langchain-openai python-dotenv pytest pydantic typing-extensions
```

Create `.env` from `.env.example`.

```powershell
copy .env.example .env
```

Edit `.env` and set your DashScope API key.

```env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

## Run the auto-approve final workflow

```powershell
python tests\test_final_auto_approve.py
```

Expected result:

```text
Patch validation status: valid
Review status: approved
Patch status: applied
Test status: passed
```

## Run the human-review workflow

```powershell
python tests\test_final_human_review.py
```

This run pauses at the human review step, then resumes with:

```python
Command(resume={"decision": "approve"})
```

## Run demo scripts

Auto-approve demo:

```powershell
python examples\final_auto_approve_demo.py
```

Human-review demo:

```powershell
python examples\final_human_review_demo.py
```

## Demo issue

RepoPilot is tested against a small demo repository.

Issue:

```text
Profile page crashes when user id does not exist.
```

Root cause:

```text
get_user_profile() calls get_user(user_id), but get_user() returns None for missing users. get_user_profile() then accesses user["name"] and user["email"] on None, causing a TypeError.
```

Expected patch:

```python
if user is None:
    return {
        "display_name": "Unknown user",
        "email": "",
    }
```

## Example final output

```text
PR Title:
Fix profile page crash for non-existent user IDs

Patch status:
applied

Test status:
passed

Final summary:
This change safely handles non-existent user IDs by returning a default profile dictionary instead of crashing. The fix is isolated to app/user_service.py, maintains backward compatibility for valid users, and passes all existing tests.
```

## Resume and checkpointing

RepoPilot compiles the graph with an in-memory checkpointer.

```python
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

Runs must include a thread id.

```python
config = {
    "configurable": {
        "thread_id": "repopilot-final-demo"
    }
}
```

This is required for interrupt-based human review because LangGraph needs to save the graph state and resume from the same thread.

## Resume after human review

```python
from langgraph.types import Command

graph.stream(
    Command(resume={"decision": "approve"}),
    config=config,
    stream_mode="updates",
    subgraphs=True,
)
```

## Resume decision options

```json
{"decision": "approve", "comment": "Looks good."}
```

```json
{"decision": "reject", "comment": "Patch is unsafe."}
```

```json
{"decision": "revise", "comment": "Please change the fallback email."}
```

## What this project demonstrates

This project demonstrates practical agent engineering skills:

* designing multi-agent workflows
* building tool-calling agents
* decomposing coding tasks into specialized agents
* using LangGraph for deterministic orchestration
* using subgraphs for modular workflow design
* using interrupts for human-in-the-loop review
* using checkpointers for resumable execution
* using tests as feedback for repair workflows
* producing PR-style outputs for engineering workflows

## Resume description

RepoPilot: Multi-Agent code maintenance system built with LangGraph and LangChain. Designed a stateful agent workflow for repository scanning, code investigation, patch planning, patch proposal generation, human review, patch application, pytest validation, failure repair routing, and PR summary generation. Implemented specialized agents including Repo Navigator Agent, Planning Agent, Patch Writer Agent, Test Analyst Agent, Repair Agent, and PR Summary Agent. Integrated LangGraph StateGraph, subgraphs, conditional edges, interrupt-based human approval, checkpoint persistence, and streaming traces.
