# Benchmark 说明

RepoPilot Benchmark 是固定案例的可复现评估框架，不代表自动修复成功率声明。

## 文件

- `benchmark/cases.json`：案例元数据。
- `benchmark/fixtures/`：原始 fixture 仓库。
- `benchmark/worktrees/`：每次运行前重置的工作副本，Git 忽略。
- `benchmark/run_benchmark.py`：运行器。
- `benchmark/results/`：带时间戳的 JSON/CSV 结果，除 `.gitkeep` 外不提交。

## 案例类型

当前包含 5 个小型 fixture：

1. 用户不存在导致 `None` 或运行时异常。
2. 参数默认值或边界处理错误。
3. 测试断言或测试数据错误。
4. 文档更新。
5. 多文件调用链缺失记录处理错误。

## Dry-run

dry-run 只重置 fixture 并执行确定性的路由和检索，不调用 LLM，不生成 patch，不应用 patch，不运行测试，也不进入 repair loop。

```powershell
python benchmark/run_benchmark.py --dry-run
python benchmark/run_benchmark.py --case missing_user_profile --dry-run
python benchmark/run_benchmark.py --all --dry-run
```

dry-run 中未执行的 patch/test/repair 字段会写为 `not_executed`。

## Graph 模式

graph 模式可能调用已配置的 LLM provider：

```powershell
python benchmark/run_benchmark.py --case missing_user_profile
python benchmark/run_benchmark.py --all
```

只有在本地模型配置、成本和隐私边界都明确可接受时才运行。缺少模型配置时，脚本会清晰提示并安全退出。

## 指标含义

结果包含 route match、relevant-file hit、files-to-modify match、patch generation、patch validation、test result、repair-loop entry、status、duration 和 error message。

不要报告任何成功率，除非它来自已经审阅的带时间戳 JSON/CSV 结果。
