# RepoPilot Benchmark

本目录提供固定案例 Benchmark 框架，用于本地可复现评估。

不调用 LLM 的 dry-run：

```powershell
python benchmark/run_benchmark.py --dry-run
python benchmark/run_benchmark.py --all --dry-run
python benchmark/run_benchmark.py --case missing_user_profile --dry-run
```

真实 graph 模式可能调用本地配置的 LLM provider：

```powershell
python benchmark/run_benchmark.py --case missing_user_profile
python benchmark/run_benchmark.py --all
```

结果会写入 `benchmark/results/` 的带时间戳 JSON 和 CSV。该目录中的生成结果会被 Git 忽略，只保留 `.gitkeep`。

不要把 dry-run 结果解释为 Agent 修复成功率；dry-run 中 patch、测试和 repair loop 字段会标记为 `not_executed`。
