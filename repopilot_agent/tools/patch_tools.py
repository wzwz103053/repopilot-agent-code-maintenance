from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PatchApplyResult:
    patch_status: str
    patch: str
    modified_files: list[str]
    error: str = ""


def resolve_repo_file(repo_path: str, relative_path: str) -> Path:
    root = Path(repo_path).resolve()
    file_path = (root / relative_path).resolve()

    if not str(file_path).startswith(str(root)):
        raise ValueError(f"Unsafe path outside repo: {relative_path}")

    return file_path


def read_repo_file(repo_path: str, relative_path: str) -> str:
    file_path = resolve_repo_file(repo_path, relative_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {relative_path}")

    return file_path.read_text(encoding="utf-8")


def write_repo_file(repo_path: str, relative_path: str, content: str) -> None:
    file_path = resolve_repo_file(repo_path, relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def build_unified_diff(relative_path: str, before: str, after: str) -> str:
    before_lines = before.splitlines()
    after_lines = after.splitlines()

    diff_lines = list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
            lineterm="",
        )
    )

    return "\n".join(diff_lines) + "\n"


def validate_unified_diff(diff: str) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if not diff.strip():
        errors.append("Patch diff is empty.")

    if "--- a/" not in diff:
        errors.append("Patch must contain a source file header like '--- a/path'.")

    if "+++ b/" not in diff:
        errors.append("Patch must contain a target file header like '+++ b/path'.")

    if "@@" not in diff:
        errors.append("Patch must contain at least one hunk header starting with '@@'.")

    return len(errors) == 0, errors


def extract_modified_files_from_diff(diff: str) -> list[str]:
    files: list[str] = []

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line.removeprefix("+++ b/").strip()
            if path != "/dev/null" and path not in files:
                files.append(path)

    return files


def patch_missing_user_profile(repo_path: str) -> dict:
    """
    旧 V4-V9 兼容函数。

    当前 demo bug 的稳定规则修复：
    在 app/user_service.py:get_user_profile 中增加 None fallback。
    """
    relative_path = "app/user_service.py"
    before = read_repo_file(repo_path, relative_path)

    if 'if user is None:' in before and '"Unknown user"' in before:
        return {
            "patch_status": "already_applied",
            "patch": "Patch already applied. No changes made.",
            "modified_files": [],
        }

    old = '''def get_user_profile(user_id: str) -> dict:
    user = get_user(user_id)
    return {
        "display_name": user["name"],
        "email": user["email"],
    }
'''

    new = '''def get_user_profile(user_id: str) -> dict:
    user = get_user(user_id)

    if user is None:
        return {
            "display_name": "Unknown user",
            "email": "",
        }

    return {
        "display_name": user["name"],
        "email": user["email"],
    }
'''

    if old not in before:
        return {
            "patch_status": "skipped",
            "patch": (
                "Expected target block was not found in app/user_service.py. "
                "Manual patch generation is required."
            ),
            "modified_files": [],
        }

    after = before.replace(old, new)
    write_repo_file(repo_path, relative_path, after)

    patch = build_unified_diff(relative_path, before, after)

    return {
        "patch_status": "applied",
        "patch": patch,
        "modified_files": [relative_path],
    }


def generate_patch_from_plan(
    repo_path: str,
    issue: str,
    plan: str,
    files_to_modify: list[str],
) -> dict:
    """
    V9 兼容函数。

    后续最终版会逐步替换为：
    Patch Writer Agent -> PatchProposal -> apply_unified_diff
    """
    issue_lower = issue.lower()
    plan_lower = plan.lower()
    file_text = " ".join(files_to_modify).lower()

    if (
        "user_service.py" in file_text
        and (
            "missing" in issue_lower
            or "does not exist" in issue_lower
            or "crash" in issue_lower
            or "crashes" in issue_lower
            or "none" in plan_lower
            or "unknown user" in plan_lower
        )
    ):
        return patch_missing_user_profile(repo_path)

    return {
        "patch_status": "skipped",
        "patch": (
            "No automatic patch rule matched the current plan. "
            "Patch Writer Agent is required for this case."
        ),
        "modified_files": [],
    }


def _parse_single_file_unified_diff(diff: str) -> tuple[str, str, str]:
    """
    解析单文件 unified diff。

    返回：
    - relative_path
    - old_text_from_hunks
    - new_text_from_hunks

    注意：
    这是一个轻量级实现，适合当前 demo 和 Agent 生成的小补丁。
    复杂 patch 后面可以接 unidiff / git apply。
    """
    lines = diff.splitlines()

    old_file = None
    new_file = None

    for line in lines:
        if line.startswith("--- a/"):
            old_file = line.removeprefix("--- a/").strip()
        elif line.startswith("+++ b/"):
            new_file = line.removeprefix("+++ b/").strip()

    if not old_file or not new_file:
        raise ValueError("Patch must contain --- a/path and +++ b/path headers.")

    if old_file != new_file:
        raise ValueError(f"Renames are not supported yet: {old_file} -> {new_file}")

    old_chunks: list[str] = []
    new_chunks: list[str] = []

    in_hunk = False

    for line in lines:
        if line.startswith("@@"):
            in_hunk = True
            continue

        if not in_hunk:
            continue

        if line.startswith("\\ No newline at end of file"):
            continue

        if line.startswith("-"):
            old_chunks.append(line[1:])
        elif line.startswith("+"):
            new_chunks.append(line[1:])
        elif line.startswith(" "):
            old_chunks.append(line[1:])
            new_chunks.append(line[1:])

    return old_file, "\n".join(old_chunks), "\n".join(new_chunks)


def apply_single_file_patch(repo_path: str, diff: str) -> PatchApplyResult:
    """
    应用单文件 unified diff。

    当前策略：
    1. 从 diff 中抽出旧块和新块
    2. 在当前文件中查找旧块
    3. 替换为新块

    优点：安全、可控、适合 demo。
    缺点：不支持复杂多 hunk、多文件、rename。
    """
    is_valid, errors = validate_unified_diff(diff)

    if not is_valid:
        return PatchApplyResult(
            patch_status="invalid",
            patch=diff,
            modified_files=[],
            error="; ".join(errors),
        )

    try:
        relative_path, old_block, new_block = _parse_single_file_unified_diff(diff)
        current = read_repo_file(repo_path, relative_path)

        if new_block in current:
            return PatchApplyResult(
                patch_status="already_applied",
                patch=diff,
                modified_files=[],
            )

        if old_block not in current:
            return PatchApplyResult(
                patch_status="failed",
                patch=diff,
                modified_files=[],
                error=(
                    "The old block from the diff was not found in the current file. "
                    "The file may have changed or the patch context is invalid."
                ),
            )

        updated = current.replace(old_block, new_block, 1)
        write_repo_file(repo_path, relative_path, updated)

        return PatchApplyResult(
            patch_status="applied",
            patch=diff,
            modified_files=[relative_path],
        )

    except Exception as exc:
        return PatchApplyResult(
            patch_status="failed",
            patch=diff,
            modified_files=[],
            error=str(exc),
        )

def split_unified_diff_by_file(diff: str) -> list[str]:
    """
    Split a multi-file unified diff into single-file unified diff blocks.

    Example:
    --- a/app/a.py
    +++ b/app/a.py
    @@ ...

    --- a/app/b.py
    +++ b/app/b.py
    @@ ...

    becomes:
    [
      "--- a/app/a.py\\n+++ b/app/a.py\\n@@ ...",
      "--- a/app/b.py\\n+++ b/app/b.py\\n@@ ..."
    ]
    """
    lines = diff.splitlines()
    chunks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("--- a/"):
            if current:
                chunks.append(current)
                current = []

        if current or line.startswith("--- a/"):
            current.append(line)

    if current:
        chunks.append(current)

    return ["\n".join(chunk).strip() + "\n" for chunk in chunks if chunk]



def apply_unified_diff(repo_path: str, diff: str) -> dict:
    """
    Final patch application entry.

    Supports:
    - single-file unified diff
    - simple multi-file unified diff

    Strategy:
    1. Split multi-file diff into per-file patches.
    2. Apply each single-file patch with apply_single_file_patch().
    3. If any patch fails, stop and report the error.
    """
    diff = strip_markdown_fences(diff)

    is_valid, errors = validate_unified_diff(diff)

    if not is_valid:
        return {
            "patch_status": "invalid",
            "patch": diff,
            "modified_files": [],
            "apply_patch_error": "; ".join(errors),
        }

    file_patches = split_unified_diff_by_file(diff)

    if not file_patches:
        return {
            "patch_status": "invalid",
            "patch": diff,
            "modified_files": [],
            "apply_patch_error": "No file patch blocks found in unified diff.",
        }

    all_modified_files: list[str] = []
    already_applied_count = 0

    for file_patch in file_patches:
        result = apply_single_file_patch(repo_path, file_patch)

        if result.patch_status == "failed":
            return {
                "patch_status": "failed",
                "patch": diff,
                "modified_files": all_modified_files,
                "apply_patch_error": result.error,
            }

        if result.patch_status == "invalid":
            return {
                "patch_status": "invalid",
                "patch": diff,
                "modified_files": all_modified_files,
                "apply_patch_error": result.error,
            }

        if result.patch_status == "already_applied":
            already_applied_count += 1

        for file in result.modified_files:
            if file not in all_modified_files:
                all_modified_files.append(file)

    if all_modified_files:
        status = "applied"
    elif already_applied_count == len(file_patches):
        status = "already_applied"
    else:
        status = "skipped"

    return {
        "patch_status": status,
        "patch": diff,
        "modified_files": all_modified_files,
        "apply_patch_error": "",
    }


def strip_markdown_fences(text: str) -> str:
    content = text.strip()

    if content.startswith("```"):
        content = re.sub(r"^```(?:diff|patch)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)

    return content.strip()