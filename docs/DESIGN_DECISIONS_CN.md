# 设计取舍

## 混合 Workflow-Agent 架构

RepoPilot 使用 LangGraph 管控流程和状态，用 LangChain Agents 处理动态推理。这样可以让路由、安全检查、人工审核、补丁应用、测试和修复次数限制保持可审计。

## 先提出补丁，再写文件

Agent 生成 unified diff，不直接修改文件。只有通过 patch validation、patch safety guardrails 和 human review 之后，`apply_patch` 节点才会写入文件。

## `.env` 与运行时配置

普通模块导入不会读取 `.env`。只有真正进入 LLM 配置边界时，`load_config()` 才会按环境允许加载 dotenv 并校验 API Key。这样真实运行仍可使用本地环境变量或 `.env`，而测试、静态导入、路由和 Benchmark dry-run 不需要 API Key。

CI 设置 `PYTHON_DOTENV_DISABLED=true`。本地也可以设置 `REPOPILOT_LOAD_DOTENV=false` 显式禁用 dotenv。

## InMemorySaver

当前 checkpointer 是 `InMemorySaver`，只支持同进程内的 human-review pause/resume 和 thread-scoped state，不支持跨重启持久化恢复。

## Compatibility Modules

| 模块 | 被哪些文件引用 | 主工作流是否使用 | 类型 | 风险 |
| -- | -- | -- | -- | -- |
| `repopilot_agent.tools.plan_tools` | `nodes/plan_patch.py` | 否 | legacy compatibility | 只保证历史节点可导入，不是当前 Planning Agent 核心实现。 |
| `repopilot_agent.tools.failure_tools` | `nodes/analyze_test_failure.py` | 否 | legacy compatibility | 轻量测试失败分类器；当前 repair graph 使用 Test Analyst Agent。 |
| `repopilot_agent.tools.repair_tools` | `nodes/repair_patch.py` | 否 | legacy compatibility | 旧节点适配层，返回 skipped repair，不伪造成功。 |
| `repopilot_agent.tools.summary_tools` | `nodes/review.py` | 否 | legacy compatibility | 旧 review 节点的确定性总结 fallback。 |
| `search_tools` compatibility helpers | `nodes/analyze_issue.py`, `nodes/retrieve_code.py` | 否 | legacy compatibility | 保持历史节点导入；主图使用 Issue Router 和 Retrieval Subgraph。 |

## Benchmark 诚实性

Benchmark 框架记录路由、相关文件命中、计划修改文件、补丁生成、补丁验证、测试、repair loop 和耗时。只有真实执行并审阅 JSON/CSV 结果后，才能报告分数或成功率。
