# 发布准备说明

## 当前状态

RepoPilot 当前适合作为 GitHub 展示和求职项目：测试目录已按职责收敛，demo 脚本与 pytest 分离，新增了 Benchmark dry-run 框架、CI、双语 README 和双语技术文档。

## 验证门槛

- `python -m pytest tests -q`
- `python scripts/verify_local_setup.py`
- `python -m compileall repopilot_agent benchmark scripts`
- `python benchmark/run_benchmark.py --dry-run`

## Windows 本地 pytest 临时目录说明

如果本地 Windows Shell 的默认用户 Temp 目录不可写，可以改用仓库内临时目录运行 pytest：

```powershell
$env:PYTHON_DOTENV_DISABLED='true'
$env:REPOPILOT_LOAD_DOTENV='false'
$env:TEMP='D:\langchain_project1\repopilot\tmp'
$env:TMP='D:\langchain_project1\repopilot\tmp'
$env:TMPDIR='D:\langchain_project1\repopilot\tmp'
python -m pytest tests -q -p no:cacheprovider --basetemp tmp\pytest-repopilot
```

这只是本地环境兼容方案，不改变 CI 和正常 Linux/macOS 的测试行为。`tmp/` 是运行时目录，不应提交。

## 已具备

- 确定性 Guardrails、Issue Router、Retrieval、Patch tools、Patch Evaluator、Docs target selection 和 Benchmark helper 有测试覆盖。
- CI 不依赖 API Key。
- Benchmark 运行结果和 worktrees 被 Git 忽略。

## 尚非生产级

- 未实现持久化 checkpointer。
- Benchmark fixture 规模有限。
- 真实 LLM 表现需要按 provider 和 model version 评估。
- Patch 仍必须经过安全检查、测试验证和人工审核。
