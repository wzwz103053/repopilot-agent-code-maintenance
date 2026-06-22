# Release Readiness

## Current Status

RepoPilot is ready as a portfolio/demo project with a clearer README, reorganized no-API tests, CI configuration, local setup verification, and a fixed-case Benchmark framework.

## Verification Gates

- `python -m pytest tests -q`
- `python scripts/verify_local_setup.py`
- GitHub Actions CI runs install, compile, setup verification, and tests.
- Benchmark dry-run can be executed with `python benchmark/run_benchmark.py --all --dry-run`.

### Windows local pytest workaround

If the default Windows user Temp directory is not writable in a local shell, run pytest with a repo-local temporary base directory:

```powershell
$env:PYTHON_DOTENV_DISABLED='true'
$env:REPOPILOT_LOAD_DOTENV='false'
$env:TEMP='D:\langchain_project1\repopilot\tmp'
$env:TMP='D:\langchain_project1\repopilot\tmp'
$env:TMPDIR='D:\langchain_project1\repopilot\tmp'
python -m pytest tests -q -p no:cacheprovider --basetemp tmp\pytest-repopilot
```

This is a local-only compatibility workaround and does not change CI or normal Linux/macOS test behavior. `tmp/` is a runtime directory and should not be committed.

## Ready

- Deterministic guardrails, issue routing, retrieval, patch tools, patch evaluation checks, docs-target selection, and benchmark helper functions have unit coverage.
- Demo scripts are outside pytest test discovery.
- CI avoids API-key dependent tests.
- Generated benchmark results and worktrees are ignored by Git.

## Not Yet Production Ready

- Durable checkpoint persistence is not implemented.
- Benchmark fixtures are small and do not prove broad automatic repair capability.
- Real LLM behavior must be evaluated per provider and model version.
- Patches still require human review and test validation before trust.
