# RepoPilot Benchmark

This directory contains fixed benchmark cases and a runner for repeatable local evaluation.

Use dry-run mode when you do not want to call any LLM APIs:

```powershell
python benchmark/run_benchmark.py --dry-run
python benchmark/run_benchmark.py --all --dry-run
```

Run a single case:

```powershell
python benchmark/run_benchmark.py --case missing_user_profile --dry-run
```

Without `--dry-run`, the runner invokes the RepoPilot graph and may call configured LLM providers. Do not run graph mode unless your local environment is intentionally configured for that cost and privacy boundary.

Results are written to `benchmark/results/` as timestamped JSON and CSV files. Generated result files are ignored by Git; keep only `.gitkeep` in version control.
