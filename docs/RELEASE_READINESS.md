# Release Readiness

## Current Status

RepoPilot is ready as a portfolio/demo project with a clearer README, reorganized no-API tests, CI configuration, local setup verification, and a fixed-case Benchmark framework.

## Verification Gates

- `python -m pytest tests -q`
- `python scripts/verify_local_setup.py`
- GitHub Actions CI runs install, compile, setup verification, and tests.
- Benchmark dry-run can be executed with `python benchmark/run_benchmark.py --all --dry-run`.

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
