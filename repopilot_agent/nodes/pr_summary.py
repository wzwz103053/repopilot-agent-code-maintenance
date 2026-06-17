from repopilot_agent.agents.pr_summary_agent import run_pr_summary_agent
from repopilot_agent.state import RepoPilotState
def _format_findings_like_list(items: list[str]) -> str:
    if not items:
        return "- None"

    return "\n".join(f"- {item}" for item in items)

def _format_findings(findings: list[dict]) -> str:
    if not findings:
        return "No findings."

    lines = []

    for item in findings:
        level = item.get("level", "unknown")
        category = item.get("category", "unknown")
        source = item.get("source", "unknown")
        message = item.get("message", "")
        lines.append(f"- [{level}] {category} at {source}: {message}")

    return "\n".join(lines)


def pr_summary_node(state: RepoPilotState) -> dict:
    """
    Generate final PR summary using PR Summary Agent.

    V11:
    If guardrails blocked execution, return a deterministic blocked summary
    instead of calling the model again.
    """
    print("[graph node] pr_summary_agent")

    guardrail_status = state.get("guardrail_status", "passed")
    patch_safety_status = state.get("patch_safety_status", "passed")

    if guardrail_status == "blocked":
        findings = state.get("guardrail_findings", [])
        block_reason = state.get("guardrail_block_reason", "")

        final_summary = (
            "RepoPilot stopped before repository analysis because preflight "
            "guardrails blocked the request.\n\n"
            f"Block reason:\n{block_reason}\n\n"
            f"Findings:\n{_format_findings(findings)}"
        )

        return {
            "pr_title": "RepoPilot blocked unsafe request",
            "pr_summary": "Preflight guardrails blocked execution before analysis.",
            "validation_summary": "No patch or tests were executed.",
            "review_checklist": [
                "Review the blocked input.",
                "Remove prompt-injection or unsafe instructions.",
                "Retry with a safe issue description.",
            ],
            "final_summary": final_summary,
        }

    if patch_safety_status == "blocked":
        findings = state.get("patch_safety_findings", [])
        block_reason = state.get("patch_safety_block_reason", "")

        final_summary = (
            "RepoPilot stopped before applying the patch because patch safety "
            "guardrails blocked the generated diff.\n\n"
            f"Block reason:\n{block_reason}\n\n"
            f"Findings:\n{_format_findings(findings)}"
        )

        return {
            "pr_title": "RepoPilot blocked unsafe patch",
            "pr_summary": "Patch safety guardrails blocked the generated patch.",
            "validation_summary": "Patch was not applied and tests were not run.",
            "review_checklist": [
                "Review the generated patch.",
                "Check whether the patch modifies forbidden files.",
                "Ask Patch Writer Agent to generate a safer minimal diff.",
            ],
            "final_summary": final_summary,
        }

    issue = state.get("issue", "")
    root_cause = state.get("root_cause", "")
    plan = state.get("plan", "")
    patch = state.get("patch", state.get("patch_proposal", ""))
    modified_files = state.get("modified_files", state.get("patch_modified_files", []))
    test_command = state.get("test_command", "not_run")
    test_status = state.get("test_status", "not_run")
    test_exit_code = state.get("test_exit_code")
    test_output = state.get("test_output", "")
    risk_level = state.get("patch_risk_level", state.get("risk_level", "low"))
    safety_notes = state.get("safety_notes", [])
    issue_route = state.get("issue_route")
    issue_route_supported = state.get("issue_route_supported", True)

    if issue_route and not issue_route_supported:
        issue_route_reason = state.get("issue_route_reason", "")
        issue_route_confidence = state.get("issue_route_confidence", 0.0)

        final_summary = (
            "RepoPilot classified the request, but this route is not implemented "
            "in the current version.\n\n"
            f"Detected route: {issue_route}\n"
            f"Confidence: {issue_route_confidence}\n"
            f"Reason: {issue_route_reason}\n\n"
            "V15 currently executes only bug_fix tasks. "
            "Future versions can add dedicated subgraphs for docs_update, "
            "test_generation, refactor, and security_review."
        )

        return {
            "pr_title": f"RepoPilot route not supported: {issue_route}",
            "pr_summary": (
                f"The request was classified as {issue_route}, "
                "but this route is not implemented yet."
            ),
            "validation_summary": "No patch or tests were executed.",
            "review_checklist": [
                "Confirm that the issue route is correct.",
                "Implement a dedicated subgraph for this route.",
                "Retry the request after the route is supported.",
            ],
            "final_summary": final_summary,
        }
    patch_evaluation_status = state.get("patch_evaluation_status")

    if patch_evaluation_status == "rejected":
        feedback = state.get("patch_evaluation_feedback", "")
        blocking_issues = state.get("patch_evaluation_blocking_issues", [])
        recommendations = state.get("patch_evaluation_recommendations", [])
        attempts = state.get("patch_revision_attempts", 0)
        max_attempts = state.get("max_patch_revision_attempts", 1)

        final_summary = (
            "RepoPilot stopped before human review because Patch Evaluator rejected "
            "the generated patch.\n\n"
            f"Revision attempts: {attempts}/{max_attempts}\n\n"
            f"Evaluator feedback:\n{feedback}\n\n"
            f"Blocking issues:\n{_format_findings_like_list(blocking_issues)}\n\n"
            f"Recommendations:\n{_format_findings_like_list(recommendations)}"
        )

        return {
            "pr_title": "RepoPilot rejected low-quality patch",
            "pr_summary": "Patch Evaluator rejected the generated patch before approval.",
            "validation_summary": "Patch was not applied and tests were not run.",
            "review_checklist": [
                "Review Patch Evaluator feedback.",
                "Check whether files_to_modify and root_cause are correct.",
                "Increase max_patch_revision_attempts or improve Patch Writer prompt.",
            ],
            "final_summary": final_summary,
        }

    result = run_pr_summary_agent(
        issue=issue,
        root_cause=root_cause,
        plan=plan,
        patch=patch,
        modified_files=modified_files,
        test_command=test_command,
        test_status=test_status,
        test_exit_code=test_exit_code,
        test_output=test_output,
        risk_level=risk_level,
        safety_notes=safety_notes,
    )

    return {
        "pr_title": result.title,
        "pr_summary": result.summary,
        "validation_summary": result.validation,
        "review_checklist": result.reviewer_checklist,
        "final_summary": result.final_summary,
    }