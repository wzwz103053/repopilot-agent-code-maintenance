from typing import Any, Literal

from typing_extensions import NotRequired, TypedDict


class RepoPilotState(TypedDict):
    """
    RepoPilot 全局状态。

    这个 State 会在 LangGraph 主图和各个 subgraph 之间流动。
    每个节点只读取自己需要的字段，并返回部分 state update。
    """

    # ===== Input =====
    repo_path: str
    issue: str

    # ===== Runtime config =====
    max_repair_attempts: NotRequired[int]
    auto_approve: NotRequired[bool]
    human_review_decision: NotRequired[Literal["approve", "reject", "revise"]]
    human_review_comment: NotRequired[str]

    # ===== Repo scan =====
    code_files: NotRequired[list[str]]
    file_tree: NotRequired[str]
    repo_summary: NotRequired[str]

    # ===== Investigation Agent =====
    issue_type: NotRequired[str]
    root_cause: NotRequired[str]
    relevant_files: NotRequired[list[str]]
    evidence: NotRequired[list[str]]
    investigation_summary: NotRequired[str]

    # ===== Planning Agent =====
    files_to_modify: NotRequired[list[str]]
    plan_steps: NotRequired[list[str]]
    risk_level: NotRequired[str]
    safety_notes: NotRequired[list[str]]
    plan: NotRequired[str]

    # ===== Patch Writer Agent =====
    patch_proposal: NotRequired[str]
    patch_explanation: NotRequired[str]
    patch_modified_files: NotRequired[list[str]]
    patch_risk_level: NotRequired[str]
    patch_validation_errors: NotRequired[list[str]]
    patch_validation_status: NotRequired[str]

    # ===== Human review =====
    review_required: NotRequired[bool]
    review_status: NotRequired[str]
    review_payload: NotRequired[dict[str, Any]]

    # ===== Patch application =====
    patch: NotRequired[str]
    patch_status: NotRequired[str]
    modified_files: NotRequired[list[str]]
    apply_patch_error: NotRequired[str]

    # ===== Tests =====
    test_command: NotRequired[str]
    test_status: NotRequired[str]
    test_exit_code: NotRequired[int]
    test_output: NotRequired[str]

    # ===== Test Analyst / Repair loop =====
    failure_analysis: NotRequired[str]
    failure_type: NotRequired[str]
    failure_evidence: NotRequired[list[str]]
    repair_attempts: NotRequired[int]
    repair_status: NotRequired[str]
    repair_patch: NotRequired[str]
    repair_notes: NotRequired[list[str]]

    # ===== PR Summary Agent =====
    pr_title: NotRequired[str]
    pr_summary: NotRequired[str]
    validation_summary: NotRequired[str]
    final_summary: NotRequired[str]
    review_checklist: NotRequired[list[str]]
    # ===== Guardrails =====
    guardrail_status: NotRequired[str]
    guardrail_findings: NotRequired[list[dict[str, Any]]]
    guardrail_block_reason: NotRequired[str]

    patch_safety_status: NotRequired[str]
    patch_safety_findings: NotRequired[list[dict[str, Any]]]
    patch_safety_block_reason: NotRequired[str]

    redaction_count: NotRequired[int]
    # ===== Debug / trace =====
    agent_trace: NotRequired[list[dict[str, Any]]]
    # ===== Retrieval / Agentic RAG =====
    retrieval_status: NotRequired[str]
    retrieval_queries: NotRequired[list[str]]
    code_chunks: NotRequired[list[dict[str, Any]]]
    retrieved_chunks: NotRequired[list[dict[str, Any]]]
    retrieved_files: NotRequired[list[str]]
    retrieval_context: NotRequired[str]
    retrieval_summary: NotRequired[str]
    # ===== V15 Issue Router =====
    issue_route: NotRequired[str]
    issue_route_reason: NotRequired[str]
    issue_route_confidence: NotRequired[float]
    issue_route_supported: NotRequired[bool]
    issue_route_candidates: NotRequired[list[dict[str, Any]]]
    # ===== V16 Docs Update =====
    docs_update_status: NotRequired[str]
    docs_target_files: NotRequired[list[str]]
    docs_update_summary: NotRequired[str]
    # ===== V17 Patch Evaluation =====
    patch_evaluation_status: NotRequired[str]
    patch_evaluation_feedback: NotRequired[str]
    patch_evaluation_score: NotRequired[float]
    patch_evaluation_blocking_issues: NotRequired[list[str]]
    patch_evaluation_recommendations: NotRequired[list[str]]
    patch_revision_attempts: NotRequired[int]
    max_patch_revision_attempts: NotRequired[int]