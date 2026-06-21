from pathlib import Path

import benchmark.run_benchmark as bench
from benchmark.run_benchmark import (
    STATUS_NOT_EXECUTED,
    build_arg_parser,
    load_cases,
    reset_fixture_repo,
    run_benchmark_cases,
    select_cases,
    write_results,
)


def test_load_cases_contains_required_metadata():
    cases = load_cases()

    assert len(cases) >= 5

    first = cases[0]
    assert first.id
    assert first.issue
    assert first.issue_type
    assert first.expected_relevant_files
    assert first.expected_files_to_modify
    assert first.validation_command
    assert first.expected_outcome


def test_select_cases_by_id():
    cases = load_cases()
    selected = select_cases(cases, case_id=cases[0].id, run_all=False)

    assert selected == [cases[0]]
    assert select_cases(cases, case_id=None, run_all=True) == cases


def test_reset_fixture_repo_copies_fixture():
    case = select_cases(load_cases(), case_id="missing_user_profile", run_all=False)[0]

    reset_fixture_repo(case)

    assert case.repo_path.exists()
    assert (case.repo_path / "app" / "user_service.py").exists()
    assert Path(case.repo_path).as_posix().endswith("benchmark/worktrees/missing_user_profile")


def test_dry_run_case_does_not_generate_patch_or_tests():
    case = select_cases(load_cases(), case_id="missing_user_profile", run_all=False)[0]

    results = run_benchmark_cases([case], dry_run=True)

    assert len(results) == 1
    assert results[0]["case_id"] == "missing_user_profile"
    assert results[0]["mode"] == "dry_run"
    assert results[0]["patch_generated"] == STATUS_NOT_EXECUTED
    assert results[0]["patch_validation_result"] == STATUS_NOT_EXECUTED
    assert results[0]["test_result"] == STATUS_NOT_EXECUTED
    assert results[0]["repair_loop_entered"] == STATUS_NOT_EXECUTED
    assert results[0]["status"] in {"passed", "failed"}


def test_cli_accepts_dry_run_without_all():
    args = build_arg_parser().parse_args(["--dry-run"])

    assert args.dry_run is True
    assert args.all is False
    assert args.case_id is None


def test_write_results_outputs_json_and_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "RESULTS_DIR", tmp_path)

    result = {
        "case_id": "unit",
        "mode": "dry_run",
        "issue": "Demo issue",
        "expected_issue_type": "bug_fix",
        "actual_issue_type": "bug_fix",
        "issue_type_match": "passed",
        "relevant_files_hit": "passed",
        "files_to_modify_match": STATUS_NOT_EXECUTED,
        "patch_generated": STATUS_NOT_EXECUTED,
        "patch_validation_result": STATUS_NOT_EXECUTED,
        "test_result": STATUS_NOT_EXECUTED,
        "repair_loop_entered": STATUS_NOT_EXECUTED,
        "status": "passed",
        "duration_ms": 1.0,
        "error_message": "",
    }

    json_path, csv_path = write_results([result], dry_run=True)

    assert json_path.exists()
    assert csv_path.exists()
    assert '"mode": "dry_run"' in json_path.read_text(encoding="utf-8")
    assert "case_id,mode,issue" in csv_path.read_text(encoding="utf-8")
