from __future__ import annotations

from repopilot_agent.state import RepoPilotState


def _format_list(items: list[str]) -> str:
    if not items:
        return "- None"

    return "\n".join(f"- {item}" for item in items)


def patch_revision_node(state: RepoPilotState) -> dict:
    """
    Convert patch evaluator feedback into stronger patch writer instructions.

    Then the patch graph loops back to patch_writer_agent.
    """
    print("[subgraph node] patch_revision")

    attempts = state.get("patch_revision_attempts", 0) + 1

    feedback = state.get("patch_evaluation_feedback", "")
    blocking_issues = state.get("patch_evaluation_blocking_issues", [])
    recommendations = state.get("patch_evaluation_recommendations", [])

    original_plan = state.get("plan", "")
    original_safety_notes = state.get("safety_notes", [])

    revision_instruction = f"""
Patch revision attempt: {attempts}

The previous patch was rejected by Patch Evaluator.

Evaluator feedback:
{feedback}

Blocking issues:
{_format_list(blocking_issues)}

Recommendations:
{_format_list(recommendations)}

Important revision rules:
- Keep the patch minimal.
- Modify only files_to_modify.
- Follow the root_cause and plan_steps.
- For bug_fix, fix the direct root-cause file instead of masking the issue in a caller.
- For docs_update, modify only documentation files.
- Return a valid unified diff only.
""".strip()

    updated_plan = f"""
{original_plan}

V17 Patch Evaluator Feedback:
{revision_instruction}
""".strip()

    updated_safety_notes = list(original_safety_notes)
    updated_safety_notes.append(
        "Patch revision requested by Patch Evaluator. The next patch must address evaluator feedback."
    )

    return {
        "patch_revision_attempts": attempts,
        "plan": updated_plan,
        "safety_notes": updated_safety_notes,
        "patch_proposal": "",
        "patch_validation_status": "pending",
        "patch_validation_errors": [],
        "patch_evaluation_status": "pending",
        "patch_evaluation_feedback": revision_instruction,
    }