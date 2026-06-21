from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from repopilot_agent.tools.code_index_tools import (
    build_code_index,
    build_retrieval_queries,
    retrieve_code_chunks,
    retrieved_files_from_chunks,
)
from repopilot_agent.tools.file_tools import scan_code_files
from repopilot_agent.tools.issue_router_tools import classify_issue_route
from repopilot_agent.tools.patch_tools import validate_unified_diff


DEFAULT_CASES_PATH = PROJECT_ROOT / "benchmark" / "cases.json"
RESULTS_DIR = PROJECT_ROOT / "benchmark" / "results"
WORKTREES_DIR = PROJECT_ROOT / "benchmark" / "worktrees"

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_BLOCKED = "blocked"
STATUS_SKIPPED = "skipped"
STATUS_NOT_EXECUTED = "not_executed"


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    name: str
    issue: str
    issue_type: str
    fixture_source: Path
    repo_path: Path
    expected_relevant_files: list[str]
    expected_files_to_modify: list[str]
    validation_command: str
    expected_outcome: str


def _project_path(raw_path: str) -> Path:
    return (PROJECT_ROOT / raw_path).resolve()


def load_cases(path: Path = DEFAULT_CASES_PATH) -> list[BenchmarkCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: list[BenchmarkCase] = []

    for item in data:
        cases.append(
            BenchmarkCase(
                id=item["id"],
                name=item["name"],
                issue=item["issue"],
                issue_type=item["issue_type"],
                fixture_source=_project_path(item["fixture_source"]),
                repo_path=_project_path(item["repo_path"]),
                expected_relevant_files=list(item["expected_relevant_files"]),
                expected_files_to_modify=list(item["expected_files_to_modify"]),
                validation_command=item["validation_command"],
                expected_outcome=item["expected_outcome"],
            )
        )

    return cases


def select_cases(
    cases: list[BenchmarkCase],
    *,
    case_id: str | None,
    run_all: bool,
) -> list[BenchmarkCase]:
    if run_all:
        return cases

    if not case_id:
        raise ValueError("Use --all or --case CASE_ID.")

    selected = [case for case in cases if case.id == case_id]

    if not selected:
        available = ", ".join(case.id for case in cases)
        raise ValueError(f"Unknown case id: {case_id}. Available: {available}")

    return selected


def reset_fixture_repo(case: BenchmarkCase) -> None:
    source = case.fixture_source.resolve()
    target = case.repo_path.resolve()
    fixtures_root = (PROJECT_ROOT / "benchmark" / "fixtures").resolve()
    worktrees_root = WORKTREES_DIR.resolve()

    if fixtures_root not in source.parents:
        raise ValueError(f"Fixture source must live under {fixtures_root}: {source}")

    if worktrees_root not in target.parents:
        raise ValueError(f"Benchmark repo path must live under {worktrees_root}: {target}")

    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Fixture source does not exist: {source}")

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(source, target)


def _recall(actual: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0

    actual_set = set(actual)
    expected_set = set(expected)

    return len(actual_set.intersection(expected_set)) / len(expected_set)


def _exact_match(actual: list[str], expected: list[str]) -> bool:
    return set(actual) == set(expected)


def status_from_bool(value: bool) -> str:
    return STATUS_PASSED if value else STATUS_FAILED


def run_dry_case(case: BenchmarkCase) -> dict[str, Any]:
    code_files = scan_code_files(str(case.repo_path))
    route = classify_issue_route(
        issue=case.issue,
        code_files=code_files,
        repo_summary="",
    )
    queries = build_retrieval_queries(issue=case.issue)
    chunks = build_code_index(str(case.repo_path), code_files)
    retrieved_chunks = retrieve_code_chunks(chunks=chunks, queries=queries, top_k=8)
    retrieved_files = retrieved_files_from_chunks(retrieved_chunks)

    return {
        "issue_route": route.route,
        "issue_route_reason": route.reason,
        "issue_route_confidence": route.confidence,
        "relevant_files": retrieved_files,
        "files_to_modify": [],
        "patch_generated": STATUS_NOT_EXECUTED,
        "patch_validation_status": STATUS_NOT_EXECUTED,
        "patch_validation_errors": [],
        "test_status": STATUS_NOT_EXECUTED,
        "test_exit_code": None,
        "repair_loop_entered": STATUS_NOT_EXECUTED,
        "raw_state": {
            "code_files": code_files,
            "retrieval_queries": queries,
            "retrieved_files": retrieved_files,
        },
    }


def run_graph_case(case: BenchmarkCase) -> dict[str, Any]:
    from repopilot_agent.agent import graph

    inputs = {
        "repo_path": str(case.repo_path),
        "issue": case.issue,
        "auto_approve": True,
        "max_repair_attempts": 2,
    }
    config = {
        "configurable": {
            "thread_id": f"benchmark-{case.id}-{int(time.time() * 1000)}",
        }
    }

    state = graph.invoke(inputs, config=config)
    patch = state.get("patch_proposal") or state.get("patch") or ""
    patch_valid, patch_errors = validate_unified_diff(patch)

    return {
        "issue_route": state.get("issue_route", state.get("issue_type", "unknown")),
        "issue_route_reason": state.get("issue_route_reason", ""),
        "issue_route_confidence": state.get("issue_route_confidence", 0.0),
        "relevant_files": state.get("relevant_files", []),
        "files_to_modify": state.get("files_to_modify", []),
        "patch_generated": status_from_bool(bool(patch.strip())),
        "patch_validation_status": state.get(
            "patch_validation_status",
            "valid" if patch_valid else "invalid",
        ),
        "patch_validation_errors": state.get("patch_validation_errors", patch_errors),
        "test_status": state.get("test_status", STATUS_NOT_EXECUTED),
        "test_exit_code": state.get("test_exit_code"),
        "repair_loop_entered": status_from_bool(state.get("repair_attempts", 0) > 0),
        "raw_state": state,
    }


def summarize_case_result(
    *,
    case: BenchmarkCase,
    run_result: dict[str, Any],
    dry_run: bool,
    elapsed_seconds: float,
) -> dict[str, Any]:
    relevant_files = list(run_result.get("relevant_files", []))
    files_to_modify = list(run_result.get("files_to_modify", []))
    issue_type_match = run_result.get("issue_route") == case.issue_type
    relevant_hit = _recall(relevant_files, case.expected_relevant_files) > 0
    files_match = _exact_match(files_to_modify, case.expected_files_to_modify)
    patch_validation_result = run_result.get("patch_validation_status", "unknown")
    test_result = run_result.get("test_status", "unknown")

    if run_result.get("error_message"):
        status = STATUS_BLOCKED
    elif dry_run:
        status = STATUS_PASSED if issue_type_match and relevant_hit else STATUS_FAILED
        files_to_modify_match = STATUS_NOT_EXECUTED
    else:
        files_to_modify_match = status_from_bool(files_match)
        status = (
            STATUS_PASSED
            if (
                issue_type_match
                and relevant_hit
                and files_match
                and patch_validation_result in {"valid", STATUS_PASSED}
                and test_result == "passed"
            )
            else STATUS_FAILED
        )

    return {
        "case_id": case.id,
        "mode": "dry_run" if dry_run else "graph",
        "name": case.name,
        "issue": case.issue,
        "expected_issue_type": case.issue_type,
        "actual_issue_type": run_result.get("issue_route", "unknown"),
        "issue_type_match": status_from_bool(issue_type_match),
        "issue_route_reason": run_result.get("issue_route_reason", ""),
        "issue_route_confidence": run_result.get("issue_route_confidence", 0.0),
        "expected_relevant_files": case.expected_relevant_files,
        "actual_relevant_files": relevant_files,
        "relevant_files_hit": status_from_bool(relevant_hit),
        "relevant_files_recall": _recall(relevant_files, case.expected_relevant_files),
        "expected_files_to_modify": case.expected_files_to_modify,
        "actual_files_to_modify": files_to_modify,
        "files_to_modify_match": files_to_modify_match,
        "patch_generated": run_result.get("patch_generated", STATUS_NOT_EXECUTED),
        "patch_validation_result": patch_validation_result,
        "patch_validation_errors": run_result.get("patch_validation_errors", []),
        "test_result": test_result,
        "test_exit_code": run_result.get("test_exit_code"),
        "repair_loop_entered": run_result.get(
            "repair_loop_entered",
            STATUS_NOT_EXECUTED,
        ),
        "status": status,
        "duration_ms": round(elapsed_seconds * 1000, 3),
        "error_message": run_result.get("error_message", ""),
        "validation_command": case.validation_command,
        "expected_outcome": case.expected_outcome,
        "elapsed_seconds": elapsed_seconds,
    }


def run_benchmark_cases(
    cases: list[BenchmarkCase],
    *,
    dry_run: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for case in cases:
        started_at = time.perf_counter()
        reset_fixture_repo(case)

        try:
            run_result = run_dry_case(case) if dry_run else run_graph_case(case)
        except Exception as exc:
            run_result = {
                "issue_route": "error",
                "issue_route_reason": str(exc),
                "issue_route_confidence": 0.0,
                "relevant_files": [],
                "files_to_modify": [],
                "patch_generated": STATUS_NOT_EXECUTED,
                "patch_validation_status": STATUS_NOT_EXECUTED,
                "patch_validation_errors": [str(exc)],
                "test_status": "error",
                "test_exit_code": None,
                "repair_loop_entered": STATUS_NOT_EXECUTED,
                "error_message": f"{type(exc).__name__}: {exc}",
                "raw_state": {"error": f"{type(exc).__name__}: {exc}"},
            }

        elapsed_seconds = time.perf_counter() - started_at
        results.append(
            summarize_case_result(
                case=case,
                run_result=run_result,
                dry_run=dry_run,
                elapsed_seconds=elapsed_seconds,
            )
        )

    return results


def write_results(results: list[dict[str, Any]], *, dry_run: bool) -> tuple[Path, Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = "dry_run" if dry_run else "graph_run"
    json_path = RESULTS_DIR / f"benchmark_{timestamp}_{suffix}.json"
    csv_path = RESULTS_DIR / f"benchmark_{timestamp}_{suffix}.csv"

    payload = {
        "generated_at": timestamp,
        "mode": "dry_run" if dry_run else "graph",
        "results": results,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    fieldnames = [
        "case_id",
        "mode",
        "issue",
        "expected_issue_type",
        "actual_issue_type",
        "issue_type_match",
        "relevant_files_hit",
        "files_to_modify_match",
        "patch_generated",
        "patch_validation_result",
        "test_result",
        "repair_loop_entered",
        "status",
        "duration_ms",
        "error_message",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow({field: result.get(field) for field in fieldnames})

    return json_path, csv_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RepoPilot benchmark cases.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--case", dest="case_id", help="Run one benchmark case id.")
    group.add_argument("--all", action="store_true", help="Run all benchmark cases.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Reset fixtures and run deterministic routing/retrieval only. No LLM calls.",
    )
    return parser


def ensure_graph_mode_available() -> tuple[bool, str]:
    try:
        from repopilot_agent.config import load_config

        load_config()
        return True, ""
    except Exception as exc:
        return (
            False,
            "Graph benchmark mode requires local model configuration. "
            "Set provider environment variables or run with --dry-run. "
            f"Configuration error: {type(exc).__name__}: {exc}",
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not args.dry_run and not args.all and not args.case_id:
        parser.error("Use --all or --case CASE_ID for graph mode, or use --dry-run.")

    if args.dry_run and not args.all and not args.case_id:
        args.all = True

    if not args.dry_run:
        ok, message = ensure_graph_mode_available()
        if not ok:
            print(message)
            return 2

    cases = select_cases(
        load_cases(),
        case_id=args.case_id,
        run_all=args.all,
    )
    results = run_benchmark_cases(cases, dry_run=args.dry_run)
    json_path, csv_path = write_results(results, dry_run=args.dry_run)

    print(f"Benchmark JSON written to {json_path}")
    print(f"Benchmark CSV written to {csv_path}")

    if args.dry_run:
        print("Dry run completed without invoking RepoPilot LLM agents.")
    else:
        print("Graph run completed. Review results before reporting any scores.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
