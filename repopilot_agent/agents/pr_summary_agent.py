from textwrap import dedent

from langchain.agents import create_agent
from repopilot_agent.agents.agent_factory import create_repopilot_agent

from repopilot_agent.agents.base import get_llm, parse_agent_result
from repopilot_agent.schemas.review import PRSummary


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot PR Summary Agent.

    Your responsibility:
    Generate a clear pull request style summary for a completed code maintenance task.

    You must summarize:
    - the original issue
    - root cause
    - what changed
    - which files changed
    - how it was validated
    - risk level
    - reviewer checklist

    PR summary rules:
    1. Be concise and specific.
    2. Do not invent changed files.
    3. Do not claim tests passed unless test_status is passed.
    4. Mention the exact test command.
    5. Include a reviewer checklist.
    6. Your final answer must be valid JSON only.
    7. Use double quotes for all JSON keys and string values.
    8. Do not use Python dict syntax with single quotes.
    9. Do not wrap JSON in markdown fences.

    Final JSON schema:
    {
      "title": "string",
      "summary": "string",
      "root_cause": "string",
      "changed_files": ["path"],
      "validation": "string",
      "risk_level": "low | medium | high",
      "reviewer_checklist": ["item"],
      "final_summary": "string"
    }
    """
).strip()


def run_pr_summary_agent(
    issue: str,
    root_cause: str,
    plan: str,
    patch: str,
    modified_files: list[str],
    test_command: str,
    test_status: str,
    test_exit_code: int | None,
    test_output: str,
    risk_level: str,
    safety_notes: list[str],
) -> PRSummary:
    agent = create_repopilot_agent(
        agent_name="pr_summary_agent",
        model=get_llm(),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
    )

    user_prompt = dedent(
        f"""
        Generate a PR summary for this completed code maintenance task.

        Issue:
        {issue}

        Root cause:
        {root_cause}

        Plan:
        {plan}

        Patch:
        {patch}

        Modified files:
        {chr(10).join(f"- {file}" for file in modified_files)}

        Test command:
        {test_command}

        Test status:
        {test_status}

        Test exit code:
        {test_exit_code}

        Test output:
        {test_output}

        Risk level:
        {risk_level}

        Safety notes:
        {chr(10).join(f"- {note}" for note in safety_notes)}

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

    return parse_agent_result(result, PRSummary)