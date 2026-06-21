# Test Migration

RepoPilot tests were reorganized so `python -m pytest tests -q` runs deterministic, reproducible tests without accidentally invoking real LLM APIs. Script-style demos were moved out of pytest discovery.

## Migration Map

| Original file | Status | New location / replacement | Reason |
| --- | --- | --- | --- |
| `tests/test_v11_guardrails.py` | Migrated | `tests/unit/test_guardrails.py` | Deterministic guardrail logic. |
| `tests/test_v12_agent_middleware.py` | Migrated | `tests/unit/test_agent_middleware.py` | Middleware import checks; skips only when optional LangChain is missing. |
| `tests/test_v13_retrieval.py` | Migrated | `tests/unit/test_retrieval.py`; graph import moved to `tests/integration/test_graph_imports.py` | Retrieval scoring is unit-level; graph import is integration-level. |
| `tests/test_v14_metrics.py` | Migrated | `tests/unit/test_eval_metrics.py` | Deterministic metric helpers. |
| `tests/test_v15_issue_router.py` | Migrated | `tests/unit/test_issue_router.py`; graph import moved to `tests/integration/test_graph_imports.py` | Routing is unit-level; graph import belongs in integration. |
| `tests/test_v16_docs_update.py` | Migrated | `tests/unit/test_docs_update.py`; graph import moved to `tests/integration/test_graph_imports.py` | Docs target selection is deterministic unit logic. |
| `tests/test_v17_patch_evaluator.py` | Migrated | `tests/unit/test_patch_evaluator.py` | Deterministic patch evaluator coverage with LLM evaluator disabled. |
| `tests/test_final_repair_loop.py` | Migrated | `tests/unit/test_route_after_tests.py` | Conditional route behavior is deterministic. |
| `tests/test_final_agents_import.py` | Migrated | `tests/integration/test_agents_import.py` | Agent imports require optional LangChain dependencies. |
| `tests/test_v18_final_release.py` | Migrated | `tests/integration/test_release_readiness.py` | Release-readiness file/doc smoke checks. |
| `tests/test_v1_scan.py` | Moved to legacy demo | `examples/legacy/test_v1_scan_demo.py` | Top-level graph invocation can call real LLM; not a stable pytest unit. |
| `tests/test_v2_retrieve.py` | Moved to legacy demo | `examples/legacy/test_v2_retrieve_demo.py` | Script-style graph run. |
| `tests/test_v3_plan.py` | Moved to legacy demo | `examples/legacy/test_v3_plan_demo.py` | Script-style graph run. |
| `tests/test_v4_generate_patch.py` | Moved to legacy demo | `examples/legacy/test_v4_generate_patch_demo.py` | Script-style graph run and repository mutation risk. |
| `tests/test_v5_run_tests.py` | Moved to legacy demo | `examples/legacy/test_v5_run_tests_demo.py` | Script-style graph run. |
| `tests/test_v8_agent_investigate.py` | Moved to legacy demo | `examples/legacy/test_v8_agent_investigate_demo.py` | Requires real Agent path. |
| `tests/test_v8_1_trace.py` | Moved to legacy demo | `examples/legacy/test_v8_1_trace_demo.py` | Trace demo, not a deterministic test. |
| `tests/test_v9_multi_agent.py` | Moved to legacy demo | `examples/legacy/test_v9_multi_agent_demo.py` | Multi-agent demo can call real LLM. |
| `tests/test_v11_blocked_issue_demo.py` | Moved to legacy demo | `examples/legacy/test_v11_blocked_issue_demo.py`; replacement `tests/e2e/test_guardrail_blocked_graph.py` | Kept as demo; new e2e version avoids model calls. |
| `tests/test_v16_docs_route_demo.py` | Moved to legacy demo | `examples/legacy/test_v16_docs_route_demo.py` | Docs route demo can invoke patch/summary agents. |
| `tests/test_final_auto_approve.py` | Moved to legacy demo | `examples/legacy/test_final_auto_approve_demo.py` | Full graph demo may call real LLM and mutate fixture. |
| `tests/test_final_human_review.py` | Moved to legacy demo | `examples/legacy/test_final_human_review_demo.py` | Human-review graph demo may call real LLM. |
| `tests/final_auto_approve_demo.py` | Moved to legacy demo | `examples/legacy/final_auto_approve_demo.py` | Demo script, not pytest. |
| `tests/final_human_review_demo.py` | Migrated to demo | `examples/demos/final_human_review_demo.py` | Real interactive demo belongs under examples. |
| `tests/inal_auto_approve_demo.py` | Moved to legacy demo | `examples/legacy/inal_auto_approve_demo.py` | Historical typo preserved for traceability. |
| `tests/reset_demo_bug_project.py` | Migrated | `examples/reset_demo_bug_project.py` | Fixture reset helper used by examples and legacy demos. |

## New Tests

- `tests/unit/test_file_tools.py`
- `tests/unit/test_patch_tools.py`
- `tests/unit/test_test_tools.py`
- `tests/unit/test_benchmark_framework.py`
- `tests/integration/test_graph_imports.py`
- `tests/e2e/test_guardrail_blocked_graph.py`

## Legacy Compatibility

Historical nodes that are no longer on the main workflow are documented in `docs/DESIGN_DECISIONS.md`. Compatibility helpers exist to keep imports explicit and testable, not to claim current core capability.
