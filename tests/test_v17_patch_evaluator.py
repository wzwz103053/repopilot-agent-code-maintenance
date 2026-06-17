from repopilot_agent.agents.patch_evaluator_agent import run_patch_evaluation
from repopilot_agent.nodes.patch_revision import patch_revision_node
from repopilot_agent.nodes.route import route_after_patch_safety_guardrails


def test_v17_accepts_safe_bug_fix_patch(monkeypatch):
    monkeypatch.setenv("REPOPILOT_ENABLE_LLM_PATCH_EVALUATOR", "false")

    patch = """--- a/app/user_service.py
+++ b/app/user_service.py
@@
 def get_user_profile(user_id: str) -> dict:
     user = get_user(user_id)
+    if user is None:
+        return {"display_name": "Unknown user", "email": ""}
     return {
         "display_name": user["name"],
         "email": user["email"],
     }
"""

    result = run_patch_evaluation(
        issue_route="bug_fix",
        issue="Profile page crashes when user id does not exist.",
        root_cause="The bug is in app/user_service.py:get_user_profile because get_user returns None.",
        relevant_files=["app/user_service.py", "app/profile.py"],
        files_to_modify=["app/user_service.py"],
        plan_steps=["Add None check in get_user_profile."],
        patch=patch,
        patch_validation_status="valid",
        patch_validation_errors=[],
    )

    assert result.status == "accepted"
    assert result.score >= 0.8


def test_v17_rejects_wrong_file_for_root_cause(monkeypatch):
    monkeypatch.setenv("REPOPILOT_ENABLE_LLM_PATCH_EVALUATOR", "false")

    patch = """--- a/app/profile.py
+++ b/app/profile.py
@@
 def render_profile_page(user_id: str) -> str:
+    if user_id == "missing":
+        return "Unknown user"
     profile = get_user_profile(user_id)
"""

    result = run_patch_evaluation(
        issue_route="bug_fix",
        issue="Profile page crashes when user id does not exist.",
        root_cause="The bug is in app/user_service.py:get_user_profile because get_user returns None.",
        relevant_files=["app/user_service.py", "app/profile.py"],
        files_to_modify=["app/user_service.py"],
        plan_steps=["Add None check in get_user_profile."],
        patch=patch,
        patch_validation_status="valid",
        patch_validation_errors=[],
    )

    assert result.status == "rejected"
    assert result.blocking_issues


def test_v17_rejects_docs_update_that_modifies_source(monkeypatch):
    monkeypatch.setenv("REPOPILOT_ENABLE_LLM_PATCH_EVALUATOR", "false")

    patch = """--- a/app/user_service.py
+++ b/app/user_service.py
@@
-OLD = 1
+OLD = 2
"""

    result = run_patch_evaluation(
        issue_route="docs_update",
        issue="Update README with setup instructions.",
        root_cause="This is a documentation update request.",
        relevant_files=["README.md"],
        files_to_modify=["README.md"],
        plan_steps=["Update README.md."],
        patch=patch,
        patch_validation_status="valid",
        patch_validation_errors=[],
    )

    assert result.status == "rejected"
    assert any("docs_update" in issue for issue in result.blocking_issues)


def test_v17_patch_revision_node_updates_plan():
    state = {
        "plan": "Original plan",
        "safety_notes": ["Original safety note"],
        "patch_evaluation_feedback": "Patch modified the wrong file.",
        "patch_evaluation_blocking_issues": ["Wrong file"],
        "patch_evaluation_recommendations": ["Modify app/user_service.py"],
        "patch_revision_attempts": 0,
    }

    update = patch_revision_node(state)

    assert update["patch_revision_attempts"] == 1
    assert "Patch Evaluator Feedback" in update["plan"]
    assert update["patch_validation_status"] == "pending"
    assert update["patch_evaluation_status"] == "pending"


def test_v17_route_requires_patch_evaluation_accepted():
    assert (
        route_after_patch_safety_guardrails(
            {
                "patch_validation_status": "valid",
                "patch_evaluation_status": "accepted",
                "patch_safety_status": "passed",
            }
        )
        == "human_review"
    )

    assert (
        route_after_patch_safety_guardrails(
            {
                "patch_validation_status": "valid",
                "patch_evaluation_status": "rejected",
                "patch_safety_status": "passed",
            }
        )
        == "pr_summary"
    )