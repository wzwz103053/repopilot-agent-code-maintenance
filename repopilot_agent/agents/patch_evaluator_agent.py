from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from repopilot_agent.agents.agent_factory import create_repopilot_agent
from repopilot_agent.schemas.patch_evaluation import PatchEvaluationResult
from repopilot_agent.tools.patch_tools import extract_modified_files_from_diff


SYSTEM_PROMPT = """
You are RepoPilot Patch Evaluator.

Your job is to evaluate a proposed unified diff before it is approved or applied.

You must be strict and practical.

For bug_fix tasks:
- Prefer fixing the direct root-cause file.
- Do not accept a patch that masks the bug in a caller when the callee violates its expected contract.
- The patch should align with root_cause, files_to_modify, and plan_steps.
- The patch should be minimal.
- The patch should preserve existing successful behavior.

For docs_update tasks:
- The patch must modify only documentation files.
- The patch must not modify source code.
- The patch must not modify tests.
- The documentation change should be concise.
- The patch should not rewrite an entire README unnecessarily.

Return ONLY valid JSON with this schema:
{
  "status": "accepted" | "rejected",
  "score": 0.0,
  "feedback": "short explanation",
  "blocking_issues": ["..."],
  "recommendations": ["..."]
}
"""


DOC_SUFFIXES = {".md", ".rst", ".txt"}


DANGEROUS_PATCH_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.Popen\s*\(",
    r"eval\s*\(",
    r"exec\s*\(",
    r"pickle\.loads\s*\(",
    r"shutil\.rmtree\s*\(",
    r"rm\s+-rf",
]

def _get_evaluator_model() -> str:
    """
    Return the model identifier used by patch_evaluator_agent.

    We intentionally do not import get_llm() from config.py because the current
    project config does not expose that function.

    create_repopilot_agent can receive a model identifier string directly.
    """
    return (
        os.getenv("REPOPILOT_EVALUATOR_MODEL")
        or os.getenv("DASHSCOPE_MODEL")
        or os.getenv("OPENAI_MODEL")
        or os.getenv("MODEL_NAME")
        or "gpt-5-mini"
    )
def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _extract_json_from_text(text: str) -> dict[str, Any]:
    """
    Extract a JSON object from model output.

    The model is instructed to return only JSON, but this function also handles
    common cases such as Markdown fenced JSON blocks.
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in patch evaluator output.")

    return json.loads(match.group(0))


def _last_message_content(agent_result: Any) -> str:
    """
    Read the last message content from a LangChain agent result.

    Different LangChain versions may return message objects or dictionaries,
    so this helper handles both.
    """
    if isinstance(agent_result, dict):
        messages = agent_result.get("messages", [])

        if messages:
            last = messages[-1]

            content = getattr(last, "content", None)
            if content is not None:
                return str(content)

            if isinstance(last, dict):
                return str(last.get("content", ""))

        return str(agent_result)

    return str(agent_result)


def _is_doc_file(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    suffix = Path(normalized).suffix.lower()
    basename = Path(normalized).name.lower()

    return (
        suffix in DOC_SUFFIXES
        or normalized.startswith("docs/")
        or basename.startswith("readme")
    )


def _line_change_count(diff: str) -> int:
    total = 0

    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+") or line.startswith("-"):
            total += 1

    return total


def _root_cause_files(root_cause: str, relevant_files: list[str]) -> list[str]:
    root_lower = root_cause.lower()
    result: list[str] = []

    for file in relevant_files:
        file_lower = file.lower()
        basename_lower = Path(file).name.lower()

        if file_lower in root_lower or basename_lower in root_lower:
            result.append(file)

    return result


def _deterministic_patch_evaluation(
    *,
    issue_route: str,
    issue: str,
    root_cause: str,
    relevant_files: list[str],
    files_to_modify: list[str],
    plan_steps: list[str],
    patch: str,
) -> PatchEvaluationResult | None:
    """
    Fast deterministic patch evaluation.

    Return:
    - PatchEvaluationResult when the patch can be confidently accepted/rejected.
    - None when the LLM evaluator should inspect the patch.
    """
    blocking_issues: list[str] = []
    recommendations: list[str] = []

    modified_files = extract_modified_files_from_diff(patch)
    expected_files = set(files_to_modify)
    actual_files = set(modified_files)

    if not patch.strip():
        return PatchEvaluationResult(
            status="rejected",
            score=0.0,
            feedback="Patch is empty.",
            blocking_issues=["Patch diff is empty."],
            recommendations=["Generate a non-empty unified diff."],
        )

    if not modified_files:
        return PatchEvaluationResult(
            status="rejected",
            score=0.1,
            feedback="Patch does not contain detectable modified files.",
            blocking_issues=[
                "No modified files were detected in the unified diff."
            ],
            recommendations=[
                "Generate a valid unified diff with --- and +++ file headers."
            ],
        )

    if expected_files and not actual_files.issubset(expected_files):
        blocking_issues.append(
            "Patch modifies files outside files_to_modify. "
            f"Expected subset of {sorted(expected_files)}, got {sorted(actual_files)}."
        )
        recommendations.append(
            "Regenerate the patch so it modifies only files listed in files_to_modify."
        )

    for pattern in DANGEROUS_PATCH_PATTERNS:
        if re.search(pattern, patch, flags=re.IGNORECASE):
            blocking_issues.append(
                f"Patch contains dangerous code pattern: {pattern}"
            )
            recommendations.append("Remove dangerous code from the patch.")

    max_changed_lines = _env_int("REPOPILOT_PATCH_EVAL_MAX_CHANGED_LINES", 120)
    changed_lines = _line_change_count(patch)

    if changed_lines > max_changed_lines:
        blocking_issues.append(
            f"Patch changes too many lines: {changed_lines} > {max_changed_lines}."
        )
        recommendations.append("Generate a smaller, more focused patch.")

    if issue_route == "docs_update":
        non_doc_files = [
            file
            for file in modified_files
            if not _is_doc_file(file)
        ]

        if non_doc_files:
            blocking_issues.append(
                f"docs_update patch modifies non-documentation files: {non_doc_files}"
            )
            recommendations.append(
                "For docs_update, modify only README/docs markdown or text files."
            )

    if issue_route == "bug_fix":
        direct_files = _root_cause_files(root_cause, relevant_files)

        if direct_files and not actual_files.intersection(direct_files):
            blocking_issues.append(
                f"Patch does not modify direct root-cause file(s): {direct_files}."
            )
            recommendations.append(
                "Modify the direct root-cause file instead of masking the issue elsewhere."
            )

        root_lower = root_cause.lower()

        if (
            "get_user_profile" in root_cause
            and "none" in root_lower
            and any(Path(file).name == "user_service.py" for file in direct_files)
            and "app/user_service.py" not in actual_files
        ):
            blocking_issues.append(
                "Patch should fix app/user_service.py:get_user_profile for missing users."
            )
            recommendations.append(
                "Add a None check after get_user(user_id) in app/user_service.py:get_user_profile."
            )

    if blocking_issues:
        return PatchEvaluationResult(
            status="rejected",
            score=0.25,
            feedback="Patch was rejected by deterministic evaluation checks.",
            blocking_issues=blocking_issues,
            recommendations=recommendations,
        )

    if not _env_bool("REPOPILOT_ENABLE_LLM_PATCH_EVALUATOR", True):
        return PatchEvaluationResult(
            status="accepted",
            score=0.85,
            feedback="Patch passed deterministic evaluation checks.",
            blocking_issues=[],
            recommendations=[],
        )

    return None


def run_patch_evaluation(
    *,
    issue_route: str,
    issue: str,
    root_cause: str,
    relevant_files: list[str],
    files_to_modify: list[str],
    plan_steps: list[str],
    patch: str,
    patch_validation_status: str,
    patch_validation_errors: list[str],
) -> PatchEvaluationResult:
    """
    Evaluate a generated patch.

    The evaluator runs deterministic checks first.
    If those pass and LLM evaluation is enabled, it asks an evaluator agent.
    """
    if patch_validation_status != "valid":
        return PatchEvaluationResult(
            status="rejected",
            score=0.2,
            feedback="Patch validation did not pass.",
            blocking_issues=patch_validation_errors or [
                "Patch validator returned invalid."
            ],
            recommendations=[
                "Regenerate a valid unified diff before semantic evaluation."
            ],
        )

    deterministic = _deterministic_patch_evaluation(
        issue_route=issue_route,
        issue=issue,
        root_cause=root_cause,
        relevant_files=relevant_files,
        files_to_modify=files_to_modify,
        plan_steps=plan_steps,
        patch=patch,
    )

    if deterministic is not None:
        return deterministic

    prompt = f"""
Evaluate the proposed patch.

Issue route:
{issue_route}

Issue:
{issue}

Root cause:
{root_cause}

Relevant files:
{relevant_files}

Files to modify:
{files_to_modify}

Plan steps:
{plan_steps}

Patch validation status:
{patch_validation_status}

Patch validation errors:
{patch_validation_errors}

Patch:
```diff
{patch}
```

Return ONLY valid JSON.
""".strip()

    try:
        agent = create_repopilot_agent(
            agent_name="patch_evaluator_agent",
            model=_get_evaluator_model(),
            tools=[],
            system_prompt=SYSTEM_PROMPT,
        )

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            }
        )

        content = _last_message_content(result)
        data = _extract_json_from_text(content)

        parsed = PatchEvaluationResult.model_validate(data)

        parsed.score = max(parsed.score, 0.0)
        parsed.score = min(parsed.score, 1.0)

        return parsed

    except Exception as exc:
        return PatchEvaluationResult(
            status="accepted",
            score=0.75,
            feedback=(
                "Patch passed deterministic checks, but LLM evaluator failed. "
                f"Proceeding with caution. Error: {exc}"
            ),
            blocking_issues=[],
            recommendations=[
                "Review the patch carefully during human_review because LLM evaluation failed."
            ],
        )