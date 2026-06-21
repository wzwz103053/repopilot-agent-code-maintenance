from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BenchmarkCase:
    """
    A benchmark case describes one repository maintenance task.

    V14 starts with one stable demo case.
    Later versions can add more cases without changing the runner.
    """

    case_id: str
    name: str
    repo_path: Path
    issue: str
    reset_script: Path | None = None

    expected_root_cause_files: list[str] = field(default_factory=list)
    expected_files_to_modify: list[str] = field(default_factory=list)
    expected_modified_files: list[str] = field(default_factory=list)
    expected_retrieved_files: list[str] = field(default_factory=list)
    expected_test_status: str = "passed"


def get_default_benchmark_cases() -> list[BenchmarkCase]:
    repo_path = Path("playground_repo/demo_bug_project").resolve()
    reset_script = Path("examples/reset_demo_bug_project.py").resolve()

    return [
        BenchmarkCase(
            case_id="demo_missing_user_profile",
            name="Profile page should not crash for missing user",
            repo_path=repo_path,
            reset_script=reset_script,
            issue="Profile page crashes when user id does not exist.",
            expected_root_cause_files=["app/user_service.py"],
            expected_files_to_modify=["app/user_service.py"],
            expected_modified_files=["app/user_service.py"],
            expected_retrieved_files=[
                "app/user_service.py",
                "app/profile.py",
                "tests/test_profile.py",
            ],
            expected_test_status="passed",
        )
    ]
