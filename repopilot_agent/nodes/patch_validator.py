from __future__ import annotations

from repopilot_agent.state import RepoPilotState


def _extract_modified_files_from_diff(diff: str) -> list[str]:
    files: list[str] = []

    for line in diff.splitlines():
        if not line.startswith("+++ "):
            continue

        path = line.removeprefix("+++ ").strip()

        if path == "/dev/null":
            continue

        if path.startswith("b/"):
            path = path[2:]

        path = path.replace("\\", "/")

        if path and path not in files:
            files.append(path)

    return files


def patch_validator_node(state: RepoPilotState) -> dict:
    """
    Validate basic unified diff shape.

    Semantic patch quality is handled later by patch_evaluator_agent.
    Patch safety is handled later by patch_safety_guardrails.
    """
    print("[subgraph node] patch_validator")

    patch = state.get("patch_proposal") or state.get("patch") or ""

    errors: list[str] = []

    if not patch.strip():
        errors.append("Patch is empty.")

    if "--- " not in patch or "+++ " not in patch:
        errors.append("Patch does not look like a unified diff.")

    modified_files = _extract_modified_files_from_diff(patch)

    if not modified_files:
        errors.append("No modified files were detected in patch.")

    status = "valid" if not errors else "invalid"

    return {
        "patch_validation_status": status,
        "patch_validation_errors": errors,
        "patch_modified_files": modified_files,
    }