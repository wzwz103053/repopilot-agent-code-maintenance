from __future__ import annotations

import os
import re
from pathlib import Path

from repopilot_agent.schemas.guardrails import GuardrailFinding, GuardrailResult
from repopilot_agent.tools.patch_tools import extract_modified_files_from_diff


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+",
    r"system\s*prompt",
    r"developer\s*message",
    r"reveal\s+your\s+instructions",
    r"print\s+your\s+hidden\s+prompt",
    r"delete\s+all\s+files",
    r"exfiltrate",
    r"send\s+.*secret",
    r"read\s+.*\.env",
]


SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",
    r"lsv2_[A-Za-z0-9_\-]{20,}",
    r"api[_-]?key\s*=\s*['\"]?[^'\"\s]+",
    r"secret[_-]?key\s*=\s*['\"]?[^'\"\s]+",
    r"access[_-]?token\s*=\s*['\"]?[^'\"\s]+",
    r"DASHSCOPE_API_KEY\s*=\s*['\"]?[^'\"\s]+",
    r"OPENAI_API_KEY\s*=\s*['\"]?[^'\"\s]+",
]


FORBIDDEN_PATCH_PATHS = {
    ".env",
    ".env.local",
    ".env.production",
    ".git/config",
}


SENSITIVE_FILE_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}


DANGEROUS_PATCH_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.Popen\s*\(",
    r"eval\s*\(",
    r"exec\s*\(",
    r"pickle\.loads\s*\(",
    r"shutil\.rmtree\s*\(",
    r"rm\s+-rf",
]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def detect_prompt_injection(text: str, source: str) -> list[GuardrailFinding]:
    findings: list[GuardrailFinding] = []

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append(
                GuardrailFinding(
                    level="block",
                    category="prompt_injection",
                    message=(
                        "Potential prompt injection found. Repository or user input "
                        "appears to contain instructions that try to override the agent."
                    ),
                    source=source,
                )
            )
            break

    return findings


def detect_secret_patterns(text: str, source: str) -> list[GuardrailFinding]:
    findings: list[GuardrailFinding] = []

    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append(
                GuardrailFinding(
                    level="warning",
                    category="secret",
                    message="Potential secret or API key detected and should be redacted.",
                    source=source,
                )
            )
            break

    return findings


def redact_sensitive_text(text: str) -> tuple[str, int]:
    """
    Redact common secret patterns before sending file contents to the model.
    """
    redacted = text
    total = 0

    for pattern in SECRET_PATTERNS:
        redacted, count = re.subn(
            pattern,
            "[REDACTED_SECRET]",
            redacted,
            flags=re.IGNORECASE,
        )
        total += count

    return redacted, total


def validate_repo_path(repo_path: str) -> list[GuardrailFinding]:
    findings: list[GuardrailFinding] = []

    path = Path(repo_path).resolve()

    if not path.exists():
        findings.append(
            GuardrailFinding(
                level="block",
                category="repo_path",
                message=f"Repository path does not exist: {repo_path}",
                source="repo_path",
            )
        )
        return findings

    if not path.is_dir():
        findings.append(
            GuardrailFinding(
                level="block",
                category="repo_path",
                message=f"Repository path is not a directory: {repo_path}",
                source="repo_path",
            )
        )

    return findings


def validate_issue_text(issue: str) -> list[GuardrailFinding]:
    findings: list[GuardrailFinding] = []

    if not issue.strip():
        findings.append(
            GuardrailFinding(
                level="block",
                category="issue",
                message="Issue text is empty.",
                source="issue",
            )
        )
        return findings

    if _env_bool("REPOPILOT_BLOCK_PROMPT_INJECTION", True):
        findings.extend(detect_prompt_injection(issue, source="issue"))

    findings.extend(detect_secret_patterns(issue, source="issue"))

    return findings


def preflight_guardrail_check(repo_path: str, issue: str) -> GuardrailResult:
    findings: list[GuardrailFinding] = []

    findings.extend(validate_repo_path(repo_path))
    findings.extend(validate_issue_text(issue))

    blocked = any(item.level == "block" for item in findings)

    return GuardrailResult(
        status="blocked" if blocked else "passed",
        findings=findings,
        block_reason="; ".join(
            item.message for item in findings if item.level == "block"
        ),
    )


def validate_patch_safety(
    diff: str,
    files_to_modify: list[str],
    allow_test_file_patches: bool = False,
) -> GuardrailResult:
    findings: list[GuardrailFinding] = []

    modified_files = extract_modified_files_from_diff(diff)
    expected = set(files_to_modify)
    actual = set(modified_files)

    if not diff.strip():
        findings.append(
            GuardrailFinding(
                level="block",
                category="unsafe_patch",
                message="Patch diff is empty.",
                source="patch",
            )
        )

    if expected and actual and not actual.issubset(expected):
        findings.append(
            GuardrailFinding(
                level="block",
                category="unsafe_patch",
                message=(
                    "Patch modifies files outside files_to_modify. "
                    f"Expected subset of {sorted(expected)}, got {sorted(actual)}."
                ),
                source="patch",
            )
        )

    for path in modified_files:
        normalized = path.replace("\\", "/").lstrip("/")

        if normalized in FORBIDDEN_PATCH_PATHS:
            findings.append(
                GuardrailFinding(
                    level="block",
                    category="forbidden_file",
                    message=f"Patch attempts to modify forbidden file: {path}",
                    source=path,
                )
            )

        suffix = Path(normalized).suffix.lower()

        if suffix in SENSITIVE_FILE_SUFFIXES:
            findings.append(
                GuardrailFinding(
                    level="block",
                    category="sensitive_file",
                    message=f"Patch attempts to modify sensitive file type: {path}",
                    source=path,
                )
            )

        if normalized.startswith("tests/") and not allow_test_file_patches:
            findings.append(
                GuardrailFinding(
                    level="warning",
                    category="test_patch",
                    message=(
                        "Patch modifies tests. This is allowed only when the issue "
                        "explicitly requires test changes."
                    ),
                    source=path,
                )
            )

    for pattern in DANGEROUS_PATCH_PATTERNS:
        if re.search(pattern, diff, flags=re.IGNORECASE):
            findings.append(
                GuardrailFinding(
                    level="block",
                    category="dangerous_code",
                    message=f"Patch contains dangerous code pattern: {pattern}",
                    source="patch",
                )
            )

    if _env_bool("REPOPILOT_BLOCK_PROMPT_INJECTION", True):
        findings.extend(detect_prompt_injection(diff, source="patch"))

    findings.extend(detect_secret_patterns(diff, source="patch"))

    blocked = any(item.level == "block" for item in findings)

    return GuardrailResult(
        status="blocked" if blocked else "passed",
        findings=findings,
        block_reason="; ".join(
            item.message for item in findings if item.level == "block"
        ),
    )


def findings_to_dicts(findings: list[GuardrailFinding]) -> list[dict]:
    return [finding.model_dump() for finding in findings]