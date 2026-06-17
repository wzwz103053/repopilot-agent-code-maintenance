from __future__ import annotations

from pathlib import Path

from repopilot_agent.eval.cases import get_default_benchmark_cases
from repopilot_agent.eval.runner import run_benchmark


def main() -> None:
    cases = get_default_benchmark_cases()
    report_path = Path("reports/benchmark_report.md")

    run_benchmark(
        cases=cases,
        report_path=report_path,
    )


if __name__ == "__main__":
    main()