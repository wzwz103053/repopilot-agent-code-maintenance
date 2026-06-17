from pathlib import Path

from langchain_core.tools import tool

from repopilot_agent.tools.file_tools import scan_code_files
from repopilot_agent.tools.search_tools import read_text_file


def _safe_resolve(repo_path: str, relative_path: str) -> Path:
    root = Path(repo_path).resolve()
    file_path = (root / relative_path).resolve()

    if not str(file_path).startswith(str(root)):
        raise ValueError(f"Unsafe path outside repo: {relative_path}")

    return file_path


def make_repo_tools(repo_path: str, code_files: list[str]):
    """
    为当前 repo_path 创建一组 Agent 可调用工具。

    这些工具是真正交给 LLM Agent 使用的。
    V8.1 加入 print trace，方便观察 Agent 实际调用了哪些工具。
    """

    @tool
    def list_repo_files() -> str:
        """
        List code and document files in the repository.
        Use this first when you need to understand the repository structure.
        """
        print("[agent tool] list_repo_files")

        files = code_files or scan_code_files(repo_path)

        if not files:
            return "No code files found."

        return "\n".join(files)

    @tool
    def read_repo_file(path: str) -> str:
        """
        Read a repository file by relative path.
        Use this when you need to inspect the content of a specific file.
        """
        print(f"[agent tool] read_repo_file: {path}")

        if path not in code_files:
            available = "\n".join(code_files[:50])
            return (
                f"File not found in scanned code files: {path}\n\n"
                f"Available files include:\n{available}"
            )

        content = read_text_file(repo_path, path, max_chars=8000)

        if not content.strip():
            return f"{path} is empty."

        return f"FILE: {path}\n\n{content}"

    @tool
    def search_repo_code(query: str) -> str:
        """
        Search repository files for a keyword or symbol.
        Use this to find functions, classes, variables, or error-related code.
        """
        print(f"[agent tool] search_repo_code: {query}")

        query_lower = query.lower().strip()

        if not query_lower:
            return "Empty query."

        matches: list[str] = []

        for path in code_files:
            content = read_text_file(repo_path, path, max_chars=12000)
            content_lower = content.lower()

            if query_lower in path.lower() or query_lower in content_lower:
                lines = content.splitlines()
                hit_lines = []

                for index, line in enumerate(lines, start=1):
                    if query_lower in line.lower():
                        hit_lines.append(f"L{index}: {line}")

                    if len(hit_lines) >= 8:
                        break

                preview = "\n".join(hit_lines) if hit_lines else "Matched file path only."
                matches.append(f"FILE: {path}\n{preview}")

            if len(matches) >= 8:
                break

        if not matches:
            return f"No matches found for query: {query}"

        return "\n\n---\n\n".join(matches)

    return [list_repo_files, read_repo_file, search_repo_code]