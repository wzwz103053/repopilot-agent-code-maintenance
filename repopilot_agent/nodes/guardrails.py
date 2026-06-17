import os

from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.guardrail_tools import (
    findings_to_dicts,
    preflight_guardrail_check,
    validate_patch_safety,
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def preflight_guardrails_node(state: RepoPilotState) -> dict:
    """
    Run safety checks before scanning and analyzing the repository.
    """
    print("[graph node] preflight_guardrails")

    if not _env_bool("REPOPILOT_ENABLE_GUARDRAILS", True):
        return {
            "guardrail_status": "passed",
            "guardrail_findings": [],
            "guardrail_block_reason": "",
        }

    result = preflight_guardrail_check(
        repo_path=state["repo_path"],
        issue=state["issue"],
    )

    return {
        "guardrail_status": result.status,
        "guardrail_findings": findings_to_dicts(result.findings),
        "guardrail_block_reason": result.block_reason,
    }


def patch_safety_guardrails_node(state: RepoPilotState) -> dict:
    """
    Run safety checks on the patch proposal before human review / apply.
    """
    print("[graph node] patch_safety_guardrails")

    if not _env_bool("REPOPILOT_ENABLE_GUARDRAILS", True):
        return {
            "patch_safety_status": "passed",
            "patch_safety_findings": [],
            "patch_safety_block_reason": "",
        }

    allow_test_file_patches = _env_bool("REPOPILOT_ALLOW_TEST_FILE_PATCHES", False)

    result = validate_patch_safety(
        diff=state.get("patch_proposal", ""),
        files_to_modify=state.get("files_to_modify", []),
        allow_test_file_patches=allow_test_file_patches,
    )

    return {
        "patch_safety_status": result.status,
        "patch_safety_findings": findings_to_dicts(result.findings),
        "patch_safety_block_reason": result.block_reason,
    }