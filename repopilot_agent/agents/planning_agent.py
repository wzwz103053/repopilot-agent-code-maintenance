from textwrap import dedent

from repopilot_agent.agents.agent_factory import create_repopilot_agent

from repopilot_agent.agents.base import get_llm, parse_agent_result
from repopilot_agent.schemas.planning import PatchPlan
from repopilot_agent.tools.agent_tools import make_repo_tools


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot Planning Agent.

    Your responsibility:
    Convert repository investigation results into a minimal safe patch plan.

    You are not responsible for writing code directly.
    You are responsible for deciding:
    - which files must be modified
    - what minimal changes should be made
    - what safety constraints must be respected

    Planning rules:
    1. Distinguish relevant_files from files_to_modify.
    2. files_to_modify must be the smallest safe set of files.
    3. Do not include caller files unless the caller itself contains the direct bug.
    4. Prefer fixing the function that violates its contract.
    5. Do not modify tests unless tests are clearly wrong or the issue asks for tests.
    6. Do not include optional hardening changes.
    7. Do not propose broad rewrites.
    8. Your final answer must be valid JSON only.
    9. Use double quotes for all JSON keys and string values.
    10. Do not use Python dict syntax with single quotes.
    11. Do not wrap JSON in markdown fences.
    12. Prefer fixing the direct root-cause file over masking the bug in a caller.
    13. If root_cause explicitly names a function and file, files_to_modify should normally include that file.
    14. Do not choose a caller file merely because it can avoid the crash if the callee violates its return contract.
    15. Tests are evidence of expected behavior; do not modify tests unless the issue explicitly asks for test updates.
    16. relevant_files are for understanding. files_to_modify must be the smallest set of files that fixes the direct cause.
    17. If get_user_profile() crashes because get_user() returns None, fix get_user_profile(), not render_profile_page().

    Final JSON schema:
    {
      "files_to_modify": ["path"],
      "plan_steps": ["step"],
      "risk_level": "low | medium | high",
      "safety_notes": ["note"],
      "reasoning_summary": "string"
    }
    """
).strip()


def run_patch_planning(
    repo_path: str,
    issue: str,
    code_files: list[str],
    issue_type: str,
    root_cause: str,
    relevant_files: list[str],
    evidence: list[str],
) -> PatchPlan:
    tools = make_repo_tools(repo_path=repo_path, code_files=code_files)

    agent = create_repopilot_agent(
        agent_name="planning_agent",
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    user_prompt = dedent(
        f"""
        Create a minimal patch plan for this repository issue.

        Issue:
        {issue}

        Issue type:
        {issue_type}

        Root cause:
        {root_cause}

        Relevant files:
        {chr(10).join(f"- {file}" for file in relevant_files)}

        Evidence:
        {chr(10).join(f"- {item}" for item in evidence)}

        Scanned files:
        {chr(10).join(code_files)}

        You may call tools if you need to verify file contents.
        Return valid JSON only.
        Use double quotes for all JSON keys and string values.
        Do not include markdown fences.
        """
    ).strip()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ]
        }
    )

    return parse_agent_result(result, PatchPlan)