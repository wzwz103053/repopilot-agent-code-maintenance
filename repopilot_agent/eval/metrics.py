from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from repopilot_agent.eval.cases import BenchmarkCase


@dataclass
class CaseMetrics:
    case_id: str
    name: str

    success: bool
    test_passed: bool
    patch_applied: bool
    guardrails_passed: bool
    patch_safety_passed: bool

    files_to_modify_accuracy: float
    modified_files_accuracy: float
    retrieval_file_recall: float
    root_cause_file_hit: bool

    repair_attempts: int
    elapsed_seconds: float

    test_status: str
    patch_status: str
    final_summary: str


def _as_set(items: list[str] | None) -> set[str]:
    return set(items or [])


def exact_set_accuracy(actual: list[str] | None, expected: list[str] | None) -> float:
    actual_set = _as_set(actual)
    expected_set = _as_set(expected)

    if not expected_set and not actual_set:
        return 1.0

    if actual_set == expected_set:
        return 1.0

    return 0.0


def recall_at_any(actual: list[str] | None, expected: list[str] | None) -> float:
    actual_set = _as_set(actual)
    expected_set = _as_set(expected)

    if not expected_set:
        return 1.0

    if not actual_set:
        return 0.0

    return len(actual_set.intersection(expected_set)) / len(expected_set)


def root_cause_file_hit(root_cause: str, expected_files: list[str]) -> bool:
    root_lower = (root_cause or "").lower()

    for file in expected_files:
        if file.lower() in root_lower:
            return True

        basename = file.replace("\\", "/").split("/")[-1].lower()
        if basename in root_lower:
            return True

    return False


def evaluate_case_result(
    *,
    case: BenchmarkCase,
    result_state: dict[str, Any],
    elapsed_seconds: float,
) -> CaseMetrics:
    test_status = result_state.get("test_status", "unknown")
    patch_status = result_state.get("patch_status", "unknown")
    guardrail_status = result_state.get("guardrail_status", "unknown")
    patch_safety_status = result_state.get("patch_safety_status", "unknown")

    files_to_modify = result_state.get("files_to_modify", [])
    modified_files = result_state.get("modified_files", [])
    retrieved_files = result_state.get("retrieved_files", [])
    root_cause = result_state.get("root_cause", "")

    test_passed = test_status == case.expected_test_status
    patch_applied = patch_status == "applied"
    guardrails_passed = guardrail_status in {"passed", "unknown"}
    patch_safety_passed = patch_safety_status in {"passed", "unknown"}

    files_to_modify_accuracy = exact_set_accuracy(
        actual=files_to_modify,
        expected=case.expected_files_to_modify,
    )

    modified_files_accuracy = exact_set_accuracy(
        actual=modified_files,
        expected=case.expected_modified_files,
    )

    retrieval_file_recall = recall_at_any(
        actual=retrieved_files,
        expected=case.expected_retrieved_files,
    )

    root_hit = root_cause_file_hit(
        root_cause=root_cause,
        expected_files=case.expected_root_cause_files,
    )

    success = (
        test_passed
        and patch_applied
        and guardrails_passed
        and patch_safety_passed
        and files_to_modify_accuracy == 1.0
        and modified_files_accuracy == 1.0
        and root_hit
    )

    return CaseMetrics(
        case_id=case.case_id,
        name=case.name,
        success=success,
        test_passed=test_passed,
        patch_applied=patch_applied,
        guardrails_passed=guardrails_passed,
        patch_safety_passed=patch_safety_passed,
        files_to_modify_accuracy=files_to_modify_accuracy,
        modified_files_accuracy=modified_files_accuracy,
        retrieval_file_recall=retrieval_file_recall,
        root_cause_file_hit=root_hit,
        repair_attempts=result_state.get("repair_attempts", 0),
        elapsed_seconds=elapsed_seconds,
        test_status=test_status,
        patch_status=patch_status,
        final_summary=result_state.get("final_summary", ""),
    )


def metrics_to_dict(metrics: CaseMetrics) -> dict[str, Any]:
    return asdict(metrics)