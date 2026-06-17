from pathlib import Path


def safe_resolve(repo_path: str, relative_path: str) -> Path:
    root = Path(repo_path).resolve()
    file_path = (root / relative_path).resolve()

    if not str(file_path).startswith(str(root)):
        raise ValueError(f"Unsafe path outside repo: {relative_path}")

    return file_path


def read_text_file(
    repo_path: str,
    relative_path: str,
    max_chars: int = 12000,
) -> str:
    file_path = safe_resolve(repo_path, relative_path)

    if not file_path.exists():
        return ""

    if not file_path.is_file():
        return ""

    return file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )[:max_chars]