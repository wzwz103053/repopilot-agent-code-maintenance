# Design Decisions

## Hybrid Workflow-Agent Architecture

RepoPilot uses deterministic LangGraph nodes for control and LLM agents for repository-specific reasoning. This makes execution inspectable: routing, patch validation, safety checks, review, test execution, and repair limits are not left to an LLM prompt alone.

## Patch Proposals Before File Writes

Agents produce unified diffs instead of directly editing files. A separate apply node writes files only after validation and review. This keeps the workflow auditable and makes it easier to reject unsafe or off-plan changes.

## In-Memory Checkpointing For Now

`InMemorySaver` is sufficient for local demos with human review interrupts. It is not durable. A production version should use a persistent LangGraph checkpointer before claiming cross-restart recovery.

## Deterministic Tests By Default

CI and `python -m pytest tests -q` avoid API keys and real LLM calls. LLM demos and real Benchmark graph runs are available, but they are explicit local actions.

## Runtime Configuration Audit

RepoPilot no longer reads `.env` at ordinary module import time. `load_config()` is called only at an LLM boundary, and that is where dotenv loading and API-key validation happen. This keeps deterministic tests, routing, static imports, and Benchmark dry-run independent of model credentials while preserving normal runtime support for environment variables or a local `.env`.

`PYTHON_DOTENV_DISABLED=true` disables dotenv loading for CI and local verification. `REPOPILOT_LOAD_DOTENV=false` can also disable it explicitly.

## Compatibility Modules

| Module | Referenced by | Used by main workflow | Type | Risk |
| -- | -- | -- | -- | -- |
| `repopilot_agent.tools.plan_tools` | `nodes/plan_patch.py` | No | legacy compatibility | Lightweight adapter for historical node imports; not current planning core. |
| `repopilot_agent.tools.failure_tools` | `nodes/analyze_test_failure.py` | No | legacy compatibility | Deterministic classifier for historical node imports; current repair graph uses Test Analyst Agent. |
| `repopilot_agent.tools.repair_tools` | `nodes/repair_patch.py` | No | legacy compatibility | Returns skipped repair for old deterministic node; not a success-claiming repair engine. |
| `repopilot_agent.tools.summary_tools` | `nodes/review.py` | No | legacy compatibility | Deterministic summary fallback for legacy review node. |
| `search_tools` compatibility helpers | `nodes/analyze_issue.py`, `nodes/retrieve_code.py` | No | legacy compatibility | Kept so historical nodes import cleanly; main graph uses issue router and retrieval subgraph. |

## Benchmark Honesty

The Benchmark framework records routing, relevant-file hits, planned files, patch generation, validation, tests, repair-loop entry, and elapsed time. Scores are not reported unless a real run has been executed and the resulting JSON/CSV artifacts are reviewed.
