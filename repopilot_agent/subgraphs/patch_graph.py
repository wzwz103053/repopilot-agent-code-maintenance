from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Callable

from typing_extensions import Literal

from langgraph.graph import END, START, StateGraph

from repopilot_agent.nodes.patch_evaluator import patch_evaluator_node
from repopilot_agent.nodes.patch_revision import patch_revision_node
from repopilot_agent.state import RepoPilotState


NodeFunc = Callable[[RepoPilotState], dict]


def _extract_modified_files_from_diff(diff: str) -> list[str]:
    """
    Lightweight unified-diff file extractor.

    Reads lines like:
    --- a/app/user_service.py
    +++ b/app/user_service.py
    """
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


def _resolve_node(
    *,
    candidates: list[tuple[str, str]],
    fallback: NodeFunc,
) -> NodeFunc:
    """
    Resolve a node function from several possible historical module/function names.

    This keeps V17 compatible with earlier RepoPilot versions where the patch writer
    node may be called generate_patch_node instead of patch_writer_node.
    """
    errors: list[str] = []

    for module_name, function_name in candidates:
        try:
            module = import_module(module_name)
            func = getattr(module, function_name)
            return func
        except Exception as exc:
            errors.append(f"{module_name}.{function_name}: {type(exc).__name__}: {exc}")

    print("[patch_graph] using fallback node because no candidate resolved:")
    for error in errors:
        print(f"  - {error}")

    return fallback


def _fallback_patch_writer_node(state: RepoPilotState) -> dict:
    """
    Fallback patch writer.

    Normally RepoPilot should use your existing patch writer node from generate_patch.py
    or patch_writer_agent.py. This fallback exists only to keep graph imports stable.
    """
    print("[subgraph node] patch_writer_agent_fallback")

    issue_route = state.get("issue_route", state.get("issue_type", "bug_fix"))
    files_to_modify = state.get("files_to_modify", [])

    patch = ""

    if issue_route == "bug_fix" and "app/user_service.py" in files_to_modify:
        patch = """--- a/app/user_service.py
+++ b/app/user_service.py
@@
 def get_user_profile(user_id: str) -> dict:
     user = get_user(user_id)
+    if user is None:
+        return {
+            "display_name": "Unknown user",
+            "email": "",
+        }
     return {
         "display_name": user["name"],
         "email": user["email"],
     }
"""

    elif issue_route == "docs_update":
        target = files_to_modify[0] if files_to_modify else "README.md"

        patch = f"""--- a/{target}
+++ b/{target}
@@
+# Setup and Usage
+
+This project can be run locally after installing the required Python dependencies.
+
+```powershell
+python -m pytest
+```
+
+For RepoPilot demos, run the example scripts from the project root.
"""

    return {
        "patch": patch,
        "patch_proposal": patch,
        "patch_status": "generated" if patch else "empty",
    }


def _fallback_patch_validator_node(state: RepoPilotState) -> dict:
    """
    Fallback patch validator.

    It only checks basic unified diff shape. Your original validator, if found,
    will be used instead of this fallback.
    """
    print("[subgraph node] patch_validator_fallback")

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


patch_writer_node = _resolve_node(
    candidates=[
        ("repopilot_agent.nodes.patch_writer", "patch_writer_node"),
        ("repopilot_agent.nodes.generate_patch", "patch_writer_node"),
        ("repopilot_agent.nodes.generate_patch", "generate_patch_node"),
        ("repopilot_agent.nodes.generate_patch", "generate_patch"),
    ],
    fallback=_fallback_patch_writer_node,
)

patch_validator_node = _resolve_node(
    candidates=[
        ("repopilot_agent.nodes.patch_validator", "patch_validator_node"),
        ("repopilot_agent.nodes.patch_validator", "validate_patch_node"),
        ("repopilot_agent.nodes.generate_patch", "patch_validator_node"),
        ("repopilot_agent.nodes.generate_patch", "validate_patch_node"),
        ("repopilot_agent.nodes.generate_patch", "validate_patch"),
    ],
    fallback=_fallback_patch_validator_node,
)


def route_after_patch_evaluation(
    state: RepoPilotState,
) -> Literal["patch_revision", "__end__"]:
    """
    If Patch Evaluator rejects the patch and revision attempts remain,
    loop back through patch_revision -> patch_writer_agent.

    Otherwise end the patch subgraph and let the parent graph decide what to do next.
    """
    status = state.get("patch_evaluation_status", "accepted")
    attempts = state.get("patch_revision_attempts", 0)
    max_attempts = state.get("max_patch_revision_attempts", 1)

    if status == "rejected" and attempts < max_attempts:
        return "patch_revision"

    return END


builder = StateGraph(RepoPilotState)

builder.add_node("patch_writer_agent", patch_writer_node)
builder.add_node("patch_validator", patch_validator_node)
builder.add_node("patch_evaluator_agent", patch_evaluator_node)
builder.add_node("patch_revision", patch_revision_node)

builder.add_edge(START, "patch_writer_agent")
builder.add_edge("patch_writer_agent", "patch_validator")
builder.add_edge("patch_validator", "patch_evaluator_agent")

builder.add_conditional_edges(
    "patch_evaluator_agent",
    route_after_patch_evaluation,
)

builder.add_edge("patch_revision", "patch_writer_agent")

patch_graph = builder.compile()