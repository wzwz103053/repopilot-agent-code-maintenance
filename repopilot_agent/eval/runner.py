from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from repopilot_agent.eval.cases import BenchmarkCase
from repopilot_agent.eval.metrics import CaseMetrics, evaluate_case_result, metrics_to_dict


def reset_case(case: BenchmarkCase) -> None:
    if case.reset_script is None:
        return

    subprocess.run(
        [sys.executable, str(case.reset_script)],
        check=True,
    )


def run_case(case: BenchmarkCase) -> tuple[dict[str, Any], CaseMetrics]:
    """
    Run one benchmark case through the RepoPilot graph.
    """
    from repopilot_agent.agent import graph

    reset_case(case)

    inputs = {
        "repo_path": str(case.repo_path),
        "issue": case.issue,
        "max_repair_attempts": 2,
        "auto_approve": True,
    }

    config = {
        "configurable": {
            "thread_id": f"repopilot-benchmark-{case.case_id}-{int(time.time() * 1000)}",
        }
    }

    started_at = time.perf_counter()
    result_state = graph.invoke(inputs, config=config)
    elapsed_seconds = time.perf_counter() - started_at

    metrics = evaluate_case_result(
        case=case,
        result_state=result_state,
        elapsed_seconds=elapsed_seconds,
    )

    return result_state, metrics


def aggregate_metrics(metrics_list: list[CaseMetrics]) -> dict[str, Any]:
    total = len(metrics_list)

    if total == 0:
        return {
            "total_cases": 0,
            "success_rate": 0.0,
            "test_pass_rate": 0.0,
            "patch_apply_rate": 0.0,
            "avg_elapsed_seconds": 0.0,
            "avg_retrieval_file_recall": 0.0,
        }

    return {
        "total_cases": total,
        "success_rate": sum(item.success for item in metrics_list) / total,
        "test_pass_rate": sum(item.test_passed for item in metrics_list) / total,
        "patch_apply_rate": sum(item.patch_applied for item in metrics_list) / total,
        "files_to_modify_accuracy": (
            sum(item.files_to_modify_accuracy for item in metrics_list) / total
        ),
        "modified_files_accuracy": (
            sum(item.modified_files_accuracy for item in metrics_list) / total
        ),
        "avg_retrieval_file_recall": (
            sum(item.retrieval_file_recall for item in metrics_list) / total
        ),
        "avg_repair_attempts": (
            sum(item.repair_attempts for item in metrics_list) / total
        ),
        "avg_elapsed_seconds": (
            sum(item.elapsed_seconds for item in metrics_list) / total
        ),
    }


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_benchmark_report(
    *,
    metrics_list: list[CaseMetrics],
    output_path: Path,
) -> None:
    aggregate = aggregate_metrics(metrics_list)

    lines: list[str] = []

    lines.append("# RepoPilot V14 Benchmark Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total cases: {aggregate['total_cases']}")
    lines.append(f"- Success rate: {format_percent(aggregate['success_rate'])}")
    lines.append(f"- Test pass rate: {format_percent(aggregate['test_pass_rate'])}")
    lines.append(f"- Patch apply rate: {format_percent(aggregate['patch_apply_rate'])}")
    lines.append(
        f"- Files-to-modify accuracy: {format_percent(aggregate['files_to_modify_accuracy'])}"
    )
    lines.append(
        f"- Modified-files accuracy: {format_percent(aggregate['modified_files_accuracy'])}"
    )
    lines.append(
        f"- Retrieval file recall: {format_percent(aggregate['avg_retrieval_file_recall'])}"
    )
    lines.append(f"- Average repair attempts: {aggregate['avg_repair_attempts']:.2f}")
    lines.append(f"- Average elapsed seconds: {aggregate['avg_elapsed_seconds']:.2f}")
    lines.append("")
    lines.append("## Cases")
    lines.append("")
    lines.append(
        "| Case | Success | Test | Patch | Files to modify | Modified files | Retrieval recall | Repair attempts | Seconds |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for item in metrics_list:
        lines.append(
            "| "
            f"{item.case_id} "
            f"| {'✅' if item.success else '❌'} "
            f"| {'✅' if item.test_passed else '❌'} "
            f"| {'✅' if item.patch_applied else '❌'} "
            f"| {format_percent(item.files_to_modify_accuracy)} "
            f"| {format_percent(item.modified_files_accuracy)} "
            f"| {format_percent(item.retrieval_file_recall)} "
            f"| {item.repair_attempts} "
            f"| {item.elapsed_seconds:.2f} "
            "|"
        )

    lines.append("")
    lines.append("## Raw Metrics")
    lines.append("")
    lines.append("```json")
    lines.append(
        json.dumps(
            [metrics_to_dict(item) for item in metrics_list],
            ensure_ascii=False,
            indent=2,
        )
    )
    lines.append("```")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_benchmark(
    cases: list[BenchmarkCase],
    report_path: Path,
) -> list[CaseMetrics]:
    metrics_list: list[CaseMetrics] = []

    for case in cases:
        print("=" * 80)
        print(f"Running benchmark case: {case.case_id}")
        print("=" * 80)

        _state, metrics = run_case(case)
        metrics_list.append(metrics)

        print(f"Success: {metrics.success}")
        print(f"Test status: {metrics.test_status}")
        print(f"Patch status: {metrics.patch_status}")
        print(f"Files-to-modify accuracy: {metrics.files_to_modify_accuracy}")
        print(f"Modified-files accuracy: {metrics.modified_files_accuracy}")
        print(f"Retrieval file recall: {metrics.retrieval_file_recall}")
        print(f"Elapsed seconds: {metrics.elapsed_seconds:.2f}")

    write_benchmark_report(
        metrics_list=metrics_list,
        output_path=report_path,
    )

    print("=" * 80)
    print(f"Benchmark report written to: {report_path}")
    print("=" * 80)

    return metrics_list