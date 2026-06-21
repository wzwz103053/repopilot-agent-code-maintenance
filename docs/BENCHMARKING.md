# Benchmarking

RepoPilot Benchmark is a fixed-case framework for repeatable local evaluation. It is not a claim of repair success rate.

## Files

- `benchmark/cases.json`: case metadata.
- `benchmark/fixtures/`: baseline fixture repositories.
- `benchmark/worktrees/`: resettable working copies generated before each run and ignored by Git.
- `benchmark/run_benchmark.py`: runner.
- `benchmark/results/`: timestamped JSON/CSV outputs, ignored by Git except `.gitkeep`.

## Cases

The current suite contains five small fixtures:

1. Missing user causes `None`/runtime bug.
2. Default/boundary parameter bug.
3. Wrong test assertion/data bug.
4. Documentation update.
5. Multi-file call chain missing-record bug.

## Dry Run

Dry-run mode resets fixtures and runs deterministic routing/retrieval only. It does not call LLM APIs, generate patches, apply patches, run tests, or enter repair loops.

```powershell
python benchmark/run_benchmark.py --dry-run
python benchmark/run_benchmark.py --case missing_user_profile --dry-run
python benchmark/run_benchmark.py --all --dry-run
```

Dry-run fields for patch/test/repair are marked `not_executed`.

## Graph Mode

Graph mode may call configured LLM providers:

```powershell
python benchmark/run_benchmark.py --case missing_user_profile
python benchmark/run_benchmark.py --all
```

Use this only when local model configuration is intentionally available and acceptable for cost/privacy. Missing model configuration causes a clear, safe exit.

## Metrics

Results include route match, relevant-file hit, files-to-modify match, patch generation status, patch validation result, test result, repair-loop entry, status, duration, and error message.

Do not report success rates unless they come from a reviewed timestamped result artifact.
