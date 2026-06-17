from pathlib import Path

from repopilot_agent.eval.cases import BenchmarkCase
from repopilot_agent.eval.metrics import (
    evaluate_case_result,
    exact_set_accuracy,
    recall_at_any,
    root_cause_file_hit,
)


def test_exact_set_accuracy():
    assert exact_set_accuracy(["a.py"], ["a.py"]) == 1.0
    assert exact_set_accuracy(["a.py"], ["b.py"]) == 0.0
    assert exact_set_accuracy([], []) == 1.0


def test_recall_at_any():
    assert recall_at_any(["a.py", "b.py"], ["a.py", "c.py"]) == 0.5
    assert recall_at_any(["a.py", "b.py"], ["a.py"]) == 1.0
    assert recall_at_any([], ["a.py"]) == 0.0


def test_root_cause_file_hit():
    root_cause = "The bug is in app/user_service.py:get_user_profile."

    assert root_cause_file_hit(root_cause, ["app/user_service.py"]) is True
    assert root_cause_file_hit(root_cause, ["app/profile.py"]) is False


def test_evaluate_case_result_success():
    case = BenchmarkCase(
        case_id="unit",
        name="Unit test case",
        repo_path=Path("."),
        issue="Demo issue",
        expected_root_cause_files=["app/user_service.py"],
        expected_files_to_modify=["app/user_service.py"],
        expected_modified_files=["app/user_service.py"],
        expected_retrieved_files=["app/user_service.py", "app/profile.py"],
        expected_test_status="passed",
    )

    state = {
        "test_status": "passed",
        "patch_status": "applied",
        "guardrail_status": "passed",
        "patch_safety_status": "passed",
        "files_to_modify": ["app/user_service.py"],
        "modified_files": ["app/user_service.py"],
        "retrieved_files": ["app/user_service.py", "app/profile.py"],
        "root_cause": "The bug is in app/user_service.py:get_user_profile.",
        "repair_attempts": 0,
        "final_summary": "Done",
    }

    metrics = evaluate_case_result(
        case=case,
        result_state=state,
        elapsed_seconds=1.23,
    )

    assert metrics.success is True
    assert metrics.test_passed is True
    assert metrics.patch_applied is True
    assert metrics.files_to_modify_accuracy == 1.0
    assert metrics.modified_files_accuracy == 1.0
    assert metrics.retrieval_file_recall == 1.0