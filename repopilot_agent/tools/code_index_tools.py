from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from repopilot_agent.schemas.retrieval import CodeChunk, RetrievedChunk


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")
DEF_CLASS_RE = re.compile(r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_\.]*)", re.MULTILINE)


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
}


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
}


ISSUE_EXPANSIONS = {
    "crash": ["error", "exception", "failure", "traceback"],
    "crashes": ["error", "exception", "failure", "traceback"],
    "missing": ["none", "null", "not_found", "not found", "unknown"],
    "not": ["missing", "none", "null"],
    "exist": ["missing", "not_found", "unknown"],
    "exists": ["missing", "not_found", "unknown"],
    "user": ["user_id", "users", "profile", "user_profile"],
    "profile": ["user_profile", "display_name", "email"],
    "id": ["user_id"],
}


def tokenize(text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    return [token for token in tokens if len(token) >= 2]


def unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        normalized = item.strip()

        if not normalized:
            continue

        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result


def safe_read_repo_file(repo_path: str, relative_path: str, max_chars: int = 50000) -> str:
    root = Path(repo_path).resolve()
    target = (root / relative_path).resolve()

    if root not in target.parents and target != root:
        raise ValueError(f"Path escapes repository root: {relative_path}")

    if not target.exists() or not target.is_file():
        return ""

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except UnicodeDecodeError:
        text = target.read_text(errors="replace")

    return text[:max_chars]


def extract_symbols(content: str) -> list[str]:
    symbols: list[str] = []

    symbols.extend(DEF_CLASS_RE.findall(content))
    symbols.extend(IMPORT_RE.findall(content))

    identifier_counts = Counter(tokenize(content))

    for token, _count in identifier_counts.most_common(30):
        if "_" in token or token.endswith(("service", "profile", "page", "test")):
            symbols.append(token)

    return unique_keep_order(symbols)[:50]


def extract_keywords(file_path: str, content: str) -> list[str]:
    tokens = tokenize(file_path + "\n" + content)
    counts = Counter(tokens)

    common_stopwords = {
        "the",
        "and",
        "for",
        "from",
        "with",
        "this",
        "that",
        "return",
        "import",
        "class",
        "def",
        "none",
        "true",
        "false",
    }

    keywords = [
        token
        for token, _count in counts.most_common(40)
        if token not in common_stopwords
    ]

    return keywords[:40]


def chunk_file_content(
    file_path: str,
    content: str,
    chunk_size: int = 80,
    overlap: int = 20,
) -> list[dict]:
    lines = content.splitlines()

    if not lines:
        return []

    chunk_size = max(chunk_size, 20)
    overlap = max(min(overlap, chunk_size - 1), 0)
    step = chunk_size - overlap

    chunks: list[dict] = []

    start_index = 0

    while start_index < len(lines):
        end_index = min(start_index + chunk_size, len(lines))
        chunk_lines = lines[start_index:end_index]
        chunk_content = "\n".join(chunk_lines)

        chunk = CodeChunk(
            chunk_id=f"{file_path}:{start_index + 1}-{end_index}",
            file_path=file_path,
            start_line=start_index + 1,
            end_line=end_index,
            content=chunk_content,
            symbols=extract_symbols(chunk_content),
            keywords=extract_keywords(file_path, chunk_content),
        )

        chunks.append(chunk.model_dump())

        if end_index >= len(lines):
            break

        start_index += step

    return chunks


def build_code_index(
    repo_path: str,
    code_files: list[str],
    chunk_size: int = 80,
    overlap: int = 20,
) -> list[dict]:
    chunks: list[dict] = []

    for file_path in code_files:
        path_obj = Path(file_path)

        if any(part in DEFAULT_IGNORE_DIRS for part in path_obj.parts):
            continue

        if path_obj.suffix.lower() not in CODE_EXTENSIONS:
            continue

        content = safe_read_repo_file(repo_path, file_path)

        if not content.strip():
            continue

        chunks.extend(
            chunk_file_content(
                file_path=file_path,
                content=content,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return chunks


def build_retrieval_queries(
    issue: str,
    repo_summary: str = "",
    file_tree: str = "",
) -> list[str]:
    base_tokens = tokenize(issue)
    expanded: list[str] = []

    for token in base_tokens:
        expanded.append(token)
        expanded.extend(ISSUE_EXPANSIONS.get(token, []))

    queries = [
        issue,
        " ".join(unique_keep_order(expanded)),
    ]

    if repo_summary:
        queries.append(repo_summary)

    # File tree is useful, but can be noisy. Keep only a short hint.
    if file_tree:
        file_tree_tokens = tokenize(file_tree)
        queries.append(" ".join(file_tree_tokens[:80]))

    return unique_keep_order(queries)


def score_chunk(chunk: dict, query_terms: list[str]) -> tuple[float, list[str]]:
    file_path = chunk.get("file_path", "")
    content = chunk.get("content", "")
    symbols = chunk.get("symbols", [])
    keywords = chunk.get("keywords", [])

    file_text = file_path.lower()
    content_text = content.lower()
    symbol_text = " ".join(symbols).lower()
    keyword_text = " ".join(keywords).lower()

    score = 0.0
    reasons: list[str] = []

    for term in query_terms:
        term = term.lower().strip()

        if not term:
            continue

        if term in file_text:
            score += 8.0
            reasons.append(f"path contains '{term}'")

        if term in symbol_text:
            score += 10.0
            reasons.append(f"symbol contains '{term}'")

        if term in keyword_text:
            score += 4.0
            reasons.append(f"keyword contains '{term}'")

        count = content_text.count(term)

        if count:
            score += min(count * 2.0, 12.0)
            reasons.append(f"content contains '{term}' x{count}")

    if file_path.startswith("tests/"):
        if any(term in {"test", "expected", "should", "crash"} for term in query_terms):
            score += 3.0
            reasons.append("test file may describe expected behavior")

    if file_path.endswith(".md"):
        score -= 2.0
        reasons.append("markdown file is less likely to contain implementation fix")

    # Deduplicate reasons while keeping order.
    reasons = unique_keep_order(reasons)

    return score, reasons[:12]


def retrieve_code_chunks(
    chunks: list[dict],
    queries: list[str],
    top_k: int = 6,
) -> list[dict]:
    query_terms: list[str] = []

    for query in queries:
        query_terms.extend(tokenize(query))

    expanded_terms: list[str] = []

    for term in query_terms:
        expanded_terms.append(term)
        expanded_terms.extend(ISSUE_EXPANSIONS.get(term, []))

    query_terms = unique_keep_order(expanded_terms)

    scored: list[dict] = []

    for chunk in chunks:
        score, reasons = score_chunk(chunk, query_terms)

        if score <= 0:
            continue

        retrieved = RetrievedChunk(
            **chunk,
            score=score,
            reasons=reasons,
        )

        scored.append(retrieved.model_dump())

    scored.sort(
        key=lambda item: (
            item["score"],
            -item.get("start_line", 0),
        ),
        reverse=True,
    )

    return scored[:top_k]


def retrieved_files_from_chunks(chunks: list[dict]) -> list[str]:
    return unique_keep_order([chunk["file_path"] for chunk in chunks])


def format_retrieval_context(
    retrieved_chunks: list[dict],
    max_chars: int = 6000,
) -> str:
    if not retrieved_chunks:
        return "(no retrieved code chunks)"

    parts: list[str] = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        reasons = "; ".join(chunk.get("reasons", [])) or "matched retrieval query"

        block = (
            f"### Retrieved chunk {index}\n"
            f"FILE: {chunk['file_path']}\n"
            f"LINES: {chunk['start_line']}-{chunk['end_line']}\n"
            f"SCORE: {chunk['score']}\n"
            f"REASONS: {reasons}\n"
            f"```text\n{chunk['content']}\n```"
        )

        parts.append(block)

    context = "\n\n".join(parts)

    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[retrieval context truncated]"

    return context


def summarize_retrieval(
    chunks: list[dict],
    retrieved_chunks: list[dict],
    retrieved_files: list[str],
) -> str:
    if not chunks:
        return "No code chunks were indexed."

    if not retrieved_chunks:
        return f"Indexed {len(chunks)} chunks, but no relevant chunks were retrieved."

    files = "\n".join(f"- {file}" for file in retrieved_files)

    return (
        f"Indexed {len(chunks)} code chunks. "
        f"Retrieved {len(retrieved_chunks)} relevant chunks from "
        f"{len(retrieved_files)} file(s).\n\n"
        f"Retrieved files:\n{files}"
    )