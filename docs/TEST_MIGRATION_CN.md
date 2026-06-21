# 测试迁移说明

RepoPilot 的测试目录已重新整理，目标是让 `python -m pytest tests -q` 只运行稳定、可复现、不会误调用真实 LLM API 的测试。脚本式 demo 已移出 pytest 默认发现范围。

## 迁移映射

| 原文件 | 当前状态 | 新位置 / 替代测试 | 原因 |
| --- | --- | --- | --- |
| `tests/test_v11_guardrails.py` | 迁移 | `tests/unit/test_guardrails.py` | Guardrails 是确定性逻辑。 |
| `tests/test_v12_agent_middleware.py` | 迁移 | `tests/unit/test_agent_middleware.py` | 仅在缺少可选 LangChain 时显式 skip。 |
| `tests/test_v13_retrieval.py` | 迁移 | `tests/unit/test_retrieval.py`；graph import 移到 `tests/integration/test_graph_imports.py` | 检索评分是 unit，图构建是 integration。 |
| `tests/test_v14_metrics.py` | 迁移 | `tests/unit/test_eval_metrics.py` | 指标函数是确定性的。 |
| `tests/test_v15_issue_router.py` | 迁移 | `tests/unit/test_issue_router.py`；graph import 移到 `tests/integration/test_graph_imports.py` | 路由是 unit，graph import 是 integration。 |
| `tests/test_v16_docs_update.py` | 迁移 | `tests/unit/test_docs_update.py`；graph import 移到 `tests/integration/test_graph_imports.py` | 文档目标选择是确定性逻辑。 |
| `tests/test_v17_patch_evaluator.py` | 迁移 | `tests/unit/test_patch_evaluator.py` | LLM evaluator 关闭后可确定性测试。 |
| `tests/test_final_repair_loop.py` | 迁移 | `tests/unit/test_route_after_tests.py` | 测试验证后的条件路由是确定性的。 |
| `tests/test_final_agents_import.py` | 迁移 | `tests/integration/test_agents_import.py` | Agent imports 依赖可选 LangChain。 |
| `tests/test_v18_final_release.py` | 迁移 | `tests/integration/test_release_readiness.py` | 发布准备 smoke checks。 |
| `tests/test_v1_scan.py` | 移到 legacy demo | `examples/legacy/test_v1_scan_demo.py` | 顶层 graph invoke 可能调用真实 LLM。 |
| `tests/test_v2_retrieve.py` | 移到 legacy demo | `examples/legacy/test_v2_retrieve_demo.py` | 脚本式 graph run。 |
| `tests/test_v3_plan.py` | 移到 legacy demo | `examples/legacy/test_v3_plan_demo.py` | 脚本式 graph run。 |
| `tests/test_v4_generate_patch.py` | 移到 legacy demo | `examples/legacy/test_v4_generate_patch_demo.py` | 可能修改 fixture，不适合默认 pytest。 |
| `tests/test_v5_run_tests.py` | 移到 legacy demo | `examples/legacy/test_v5_run_tests_demo.py` | 脚本式 graph run。 |
| `tests/test_v8_agent_investigate.py` | 移到 legacy demo | `examples/legacy/test_v8_agent_investigate_demo.py` | 依赖真实 Agent 路径。 |
| `tests/test_v8_1_trace.py` | 移到 legacy demo | `examples/legacy/test_v8_1_trace_demo.py` | Trace demo，不是确定性测试。 |
| `tests/test_v9_multi_agent.py` | 移到 legacy demo | `examples/legacy/test_v9_multi_agent_demo.py` | Multi-agent demo 可能调用真实 LLM。 |
| `tests/test_v11_blocked_issue_demo.py` | 移到 legacy demo | `examples/legacy/test_v11_blocked_issue_demo.py`；替代为 `tests/e2e/test_guardrail_blocked_graph.py` | 保留 demo，新 e2e 避免模型调用。 |
| `tests/test_v16_docs_route_demo.py` | 移到 legacy demo | `examples/legacy/test_v16_docs_route_demo.py` | docs route demo 可能进入 Agent。 |
| `tests/test_final_auto_approve.py` | 移到 legacy demo | `examples/legacy/test_final_auto_approve_demo.py` | 完整 graph demo 可能调用 LLM 并修改 fixture。 |
| `tests/test_final_human_review.py` | 移到 legacy demo | `examples/legacy/test_final_human_review_demo.py` | human-review demo 可能调用 LLM。 |
| `tests/final_auto_approve_demo.py` | 移到 legacy demo | `examples/legacy/final_auto_approve_demo.py` | demo 脚本不应在 tests 中。 |
| `tests/final_human_review_demo.py` | 迁移为 demo | `examples/demos/final_human_review_demo.py` | 交互式 demo 放入 examples。 |
| `tests/inal_auto_approve_demo.py` | 移到 legacy demo | `examples/legacy/inal_auto_approve_demo.py` | 保留历史拼写错误以便追踪。 |
| `tests/reset_demo_bug_project.py` | 迁移 | `examples/reset_demo_bug_project.py` | fixture reset helper 供 examples 使用。 |

## 新增测试

- `tests/unit/test_file_tools.py`
- `tests/unit/test_patch_tools.py`
- `tests/unit/test_test_tools.py`
- `tests/unit/test_benchmark_framework.py`
- `tests/integration/test_graph_imports.py`
- `tests/e2e/test_guardrail_blocked_graph.py`

## Legacy Compatibility

不再进入主工作流的历史节点和兼容模块已在 `docs/DESIGN_DECISIONS.md` 中记录。兼容层用于保持旧节点导入清晰可测，不代表当前核心能力。
