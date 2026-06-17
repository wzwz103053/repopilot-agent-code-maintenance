from textwrap import dedent

from repopilot_agent.agents.agent_factory import create_repopilot_agent

from repopilot_agent.agents.base import get_llm, parse_agent_result
from repopilot_agent.schemas.testing import TestFailureAnalysis
from repopilot_agent.tools.repo_tools import make_repo_tools


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot Test Analyst Agent.

    Your responsibility:
    Analyze failed test output and classify why the validation failed.

    You do not write patches.
    You only analyze the test failure and recommend the next action.

    Available tools:
    - list_repo_files: inspect repository structure
    - search_repo_code: search for symbols, functions, errors
    - read_repo_file: read repository file contents

    Failure analysis rules:
    1. Focus on the pytest output first.
    2. Use repository tools only when you need to understand a referenced file or symbol.
    3. Distinguish implementation failures from environment failures.
    4. If the patch did not apply, classify it as patch_did_not_apply.
    5. If tests fail because behavior is still wrong, classify it as wrong_fix or assertion_failure.
    6. If there is an import problem, classify it as import_error.
    7. If tests passed, classify failure_type as none and suggested_next_action as stop.
    8. Your final answer must be valid JSON only.
    9. Use double quotes for all JSON keys and string values.
    10. Do not use Python dict syntax with single quotes.
    11. Do not wrap JSON in markdown fences.

    Final JSON schema:
    {
      "failure_type": "none | import_error | assertion_failure | runtime_error | patch_did_not_apply | wrong_fix | environment_error | unknown",
      "failure_analysis": "string",
      "failure_evidence": ["evidence"],
      "suggested_next_action": "rerun_tests | repair_patch | ask_human | stop",
      "affected_files": ["path"]
    }
    """
).strip()


def run_test_analysis(
    repo_path: str,
    issue: str,
    code_files: list[str],
    test_command: str,
    test_status: str,
    test_exit_code: int | None,
    test_output: str,
    patch: str,
    modified_files: list[str],
) -> TestFailureAnalysis:
    tools = make_repo_tools(repo_path=repo_path, code_files=code_files)

    agent = create_repopilot_agent(
        agent_name="test_analyst_agent",
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    user_prompt = dedent(
        f"""
        Analyze this test result.

        Issue:
        {issue}

        Test command:
        {test_command}

        Test status:
        {test_status}

        Test exit code:
        {test_exit_code}

        Modified files:
        {chr(10).join(f"- {file}" for file in modified_files)}

        Patch:
        {patch}

        Test output:
        {test_output}

        Scanned files:
        {chr(10).join(code_files)}

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

    return parse_agent_result(result, TestFailureAnalysis)