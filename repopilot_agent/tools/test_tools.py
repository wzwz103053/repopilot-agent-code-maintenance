import subprocess
import sys
from pathlib import Path


def resolve_repo_path(repo_path: str) -> Path:
    root = Path(repo_path).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Repo path does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Repo path is not a directory: {root}")

    return root


def infer_test_command(repo_path: str) -> list[str]:
    """
    根据仓库结构推断测试命令。

    当前 demo 项目是 Python 项目，所以运行 pytest tests。
    使用 sys.executable -m pytest 可以确保使用当前虚拟环境里的 pytest。
    """
    root = resolve_repo_path(repo_path)

    if (root / "tests").exists():
        return [sys.executable, "-m", "pytest", "tests"]

    return [sys.executable, "-m", "pytest"]


def run_test_command(
    repo_path: str,
    command: list[str] | None = None,
    timeout_seconds: int = 30,
) -> dict:
    root = resolve_repo_path(repo_path)

    if command is None:
        command = infer_test_command(repo_path)

    command_text = " ".join(command)

    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        output = ""
        if completed.stdout:
            output += completed.stdout

        if completed.stderr:
            output += "\n[stderr]\n"
            output += completed.stderr

        test_status = "passed" if completed.returncode == 0 else "failed"

        return {
            "test_command": command_text,
            "test_status": test_status,
            "test_exit_code": completed.returncode,
            "test_output": output.strip(),
        }

    except subprocess.TimeoutExpired as exc:
        output = ""

        if exc.stdout:
            output += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode(errors="ignore")

        if exc.stderr:
            output += "\n[stderr]\n"
            output += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode(errors="ignore")

        return {
            "test_command": command_text,
            "test_status": "timeout",
            "test_exit_code": -1,
            "test_output": output.strip() or f"Test command timed out after {timeout_seconds} seconds.",
        }