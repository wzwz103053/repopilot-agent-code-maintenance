from pathlib import Path


def analyze_issue_text(issue: str) -> dict:
    """Compatibility helper for older deterministic nodes."""
    issue_lower = issue.lower()

    if any(word in issue_lower for word in ["crash", "bug", "error", "fail"]):
        issue_type = "bug_fix"
    elif any(word in issue_lower for word in ["readme", "docs", "documentation"]):
        issue_type = "documentation"
    elif "test" in issue_lower:
        issue_type = "test_request"
    else:
        issue_type = "unknown"

    keywords = [
        token.strip(".,:;!?()[]{}\"'")
        for token in issue_lower.split()
        if len(token.strip(".,:;!?()[]{}\"'")) >= 3
    ]

    return {
        "issue_type": issue_type,
        "issue_keywords": sorted(set(keywords)),
        "issue_summary": issue.strip(),
    }


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


def retrieve_relevant_files(
    repo_path: str,
    files: list[str],
    keywords: list[str],
    issue_type: str = "unknown",
    top_k: int = 5,
) -> list[dict]:
    """Small deterministic retriever kept for legacy node compatibility."""
    scored: list[dict] = []
    normalized_keywords = [keyword.lower() for keyword in keywords if keyword]

    for relative_path in files:
        content = read_text_file(repo_path, relative_path, max_chars=12000)
        haystack = f"{relative_path}\n{content}".lower()
        reasons: list[str] = []
        score = 0

        for keyword in normalized_keywords:
            count = haystack.count(keyword)
            if count:
                score += count
                reasons.append(f"matched '{keyword}' x{count}")

        if issue_type == "bug_fix" and relative_path.endswith(".py"):
            score += 1
            reasons.append("python source/test file for bug_fix")

        if score <= 0:
            continue

        snippet = "\n".join(content.splitlines()[:20])
        scored.append(
            {
                "path": relative_path,
                "score": score,
                "reasons": reasons,
                "snippet": snippet,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def format_retrieval_summary(retrieved_files: list[dict]) -> str:
    if not retrieved_files:
        return "No relevant files were retrieved."

    lines = ["Retrieved relevant files:"]

    for item in retrieved_files:
        path = item.get("path", "unknown")
        score = item.get("score", 0)
        lines.append(f"- {path} (score={score})")

    return "\n".join(lines)
