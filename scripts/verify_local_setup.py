from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_CASE_FIELDS = {
    "id",
    "issue",
    "issue_type",
    "expected_relevant_files",
    "expected_files_to_modify",
    "validation_command",
    "expected_outcome",
}

REQUIRED_PATHS = [
    "README.md",
    "README_CN.md",
    "pyproject.toml",
    "langgraph.json",
    ".env.example",
    "docs/ARCHITECTURE.md",
    "docs/ARCHITECTURE_CN.md",
    "docs/BENCHMARKING.md",
    "docs/BENCHMARKING_CN.md",
    "docs/DESIGN_DECISIONS.md",
    "docs/DESIGN_DECISIONS_CN.md",
    "docs/TEST_MIGRATION.md",
    "docs/TEST_MIGRATION_CN.md",
    "docs/RELEASE_READINESS.md",
    "docs/RELEASE_READINESS_CN.md",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "examples/demos",
    "examples/legacy",
    "examples/reset_demo_bug_project.py",
    "playground_repo/demo_bug_project",
    "benchmark/cases.json",
    "benchmark/run_benchmark.py",
    "benchmark/README.md",
    "benchmark/README_CN.md",
    "benchmark/results/.gitkeep",
]

REQUIRED_IMPORTS = [
    "repopilot_agent.tools.file_tools",
    "repopilot_agent.tools.patch_tools",
    "repopilot_agent.tools.guardrail_tools",
    "repopilot_agent.tools.issue_router_tools",
    "repopilot_agent.tools.code_index_tools",
    "benchmark.run_benchmark",
]

OPTIONAL_IMPORTS = [
    "repopilot_agent.agent",
    "repopilot_agent.agents.agent_factory",
]

README_PATH_REFERENCES = [
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "examples/demos/final_auto_approve_demo.py",
    "examples/demos/final_docs_update_demo.py",
    "examples/demos/final_human_review_demo.py",
    "benchmark/run_benchmark.py",
    "docs/ARCHITECTURE.md",
    "docs/BENCHMARKING.md",
]


def emit(status: str, message: str) -> None:
    print(f"[{status}] {message}")


def check_required_paths() -> list[str]:
    failures: list[str] = []

    for relative_path in REQUIRED_PATHS:
        path = PROJECT_ROOT / relative_path
        if path.exists():
            emit("PASS", f"{relative_path} exists")
        else:
            emit("FAIL", f"expected {relative_path} is missing")
            failures.append(relative_path)

    return failures


def check_cases_schema() -> list[str]:
    path = PROJECT_ROOT / "benchmark" / "cases.json"
    failures: list[str] = []

    try:
        cases = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        emit("FAIL", f"benchmark/cases.json could not be parsed: {exc}")
        return ["benchmark/cases.json"]

    if not isinstance(cases, list) or len(cases) < 5:
        emit("FAIL", "benchmark/cases.json must contain at least five cases")
        failures.append("benchmark/cases.json")
        return failures

    seen_ids: set[str] = set()

    for index, case in enumerate(cases, start=1):
        missing = REQUIRED_CASE_FIELDS.difference(case)

        if missing:
            emit("FAIL", f"benchmark case #{index} missing fields: {sorted(missing)}")
            failures.append(f"case#{index}")
            continue

        if case["id"] in seen_ids:
            emit("FAIL", f"duplicate benchmark case id: {case['id']}")
            failures.append(case["id"])

        seen_ids.add(case["id"])

    if not failures:
        emit("PASS", "benchmark/cases.json schema is valid")

    return failures


def check_required_imports() -> list[str]:
    failures: list[str] = []

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            emit("FAIL", f"import {module_name}: {type(exc).__name__}: {exc}")
            failures.append(module_name)
        else:
            emit("PASS", f"import {module_name}")

    return failures


def check_optional_imports() -> None:
    for module_name in OPTIONAL_IMPORTS:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            emit("WARN", f"optional import skipped: {module_name} ({exc.name} missing)")
        except Exception as exc:
            emit(
                "WARN",
                f"optional import unavailable: {module_name} ({type(exc).__name__}: {exc})",
            )
        else:
            emit("PASS", f"optional import {module_name}")


def check_readme_references() -> list[str]:
    failures: list[str] = []
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    for relative_path in README_PATH_REFERENCES:
        if relative_path in readme and (PROJECT_ROOT / relative_path).exists():
            emit("PASS", f"README reference exists: {relative_path}")
        else:
            emit("FAIL", f"README reference missing or not documented: {relative_path}")
            failures.append(relative_path)

    return failures


def check_test_discovery() -> list[str]:
    env = os.environ.copy()
    env["PYTHON_DOTENV_DISABLED"] = "true"

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    if completed.returncode == 0:
        emit("PASS", "pytest can discover tests")
        return []

    emit("FAIL", "pytest discovery failed")
    output = "\n".join(
        part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
    )
    if output:
        print(output)

    return ["pytest discovery"]


def main() -> int:
    os.chdir(PROJECT_ROOT)

    print("RepoPilot local setup verification")
    print(f"Project root: {PROJECT_ROOT}")
    emit("WARN", ".env is intentionally not inspected")

    failures: list[str] = []
    failures.extend(check_required_paths())
    failures.extend(check_cases_schema())
    failures.extend(check_required_imports())
    check_optional_imports()
    failures.extend(check_readme_references())
    failures.extend(check_test_discovery())

    if failures:
        emit("FAIL", f"verification failed with {len(failures)} issue(s)")
        return 1

    emit("PASS", "verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
