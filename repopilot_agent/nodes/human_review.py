from langgraph.types import interrupt

from repopilot_agent.state import RepoPilotState


def _env_bool(name: str, default: bool) -> bool:
    import os

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def human_review_node(state: RepoPilotState) -> dict:
    """
    Human-in-the-loop patch review node.

    默认 auto_approve=True 时自动通过，方便本地测试。
    当 auto_approve=False 时，使用 LangGraph interrupt 暂停流程，等待人工审核。
    """
    print("[graph node] human_review")

    auto_approve = state.get(
        "auto_approve",
        _env_bool("REPOPILOT_AUTO_APPROVE", True),
    )

    payload = {
        "action": "review_patch",
        "issue": state.get("issue", ""),
        "root_cause": state.get("root_cause", ""),
        "files_to_modify": state.get("files_to_modify", []),
        "patch_proposal": state.get("patch_proposal", ""),
        "patch_explanation": state.get("patch_explanation", ""),
        "patch_modified_files": state.get("patch_modified_files", []),
        "patch_risk_level": state.get("patch_risk_level", ""),
        "safety_notes": state.get("safety_notes", []),
        "instructions": (
            "Approve, reject, or request revision for this patch proposal. "
            "Return {'decision': 'approve'} to apply the patch."
        ),
    }

    if auto_approve:
        return {
            "review_required": False,
            "review_status": "approved",
            "human_review_decision": "approve",
            "human_review_comment": "Auto-approved by REPOPILOT_AUTO_APPROVE=true.",
            "review_payload": payload,
        }

    human_response = interrupt(payload)

    decision = "reject"
    comment = ""

    if isinstance(human_response, bool):
        decision = "approve" if human_response else "reject"
    elif isinstance(human_response, str):
        decision = human_response.strip().lower()
    elif isinstance(human_response, dict):
        decision = str(human_response.get("decision", "reject")).strip().lower()
        comment = str(human_response.get("comment", ""))

    if decision not in {"approve", "reject", "revise"}:
        decision = "reject"

    review_status = {
        "approve": "approved",
        "reject": "rejected",
        "revise": "revision_requested",
    }[decision]

    return {
        "review_required": True,
        "review_status": review_status,
        "human_review_decision": decision,
        "human_review_comment": comment,
        "review_payload": payload,
    }
