from collections import Counter
from pathlib import Path


SUPPORTED_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
}

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
}


def scan_code_files(repo_path: str) -> list[str]:
    root = Path(repo_path).resolve()
    files: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in IGNORED_DIRS for part in path.parts):
            continue

        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        files.append(path.relative_to(root).as_posix())

    return sorted(files)


def build_file_tree(code_files: list[str]) -> str:
    if not code_files:
        return "(empty repository)"

    return "\n".join(f"- {file}" for file in code_files)


def summarize_repo_files(code_files: list[str]) -> str:
    if not code_files:
        return "Found 0 code/document files."

    counter = Counter(Path(file).suffix or "(no suffix)" for file in code_files)

    suffix_summary = ", ".join(
        f"{suffix}: {count}"
        for suffix, count in sorted(counter.items())
    )

    return f"Found {len(code_files)} code/document files. File types: {suffix_summary}"