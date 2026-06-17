from textwrap import dedent

from repopilot_agent.agents.agent_factory import create_repopilot_agent

from repopilot_agent.agents.base import get_llm, parse_agent_result
from repopilot_agent.schemas.investigation import RepoNavigationResult
from repopilot_agent.tools.agent_tools import make_repo_tools


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot Repo Navigator Agent.

    Your responsibility:
    Investigate the repository issue by reading files and collecting evidence.

    You are not responsible for writing the patch.
    You are not responsible for deciding the exact implementation plan.
    Another Planning Agent will do that after you.

    Available tools:
    - list_repo_files: inspect repository structure
    - search_repo_code: search for symbols, keywords, functions, or errors
    - read_repo_file: inspect file contents

    Investigation rules:
    1. You must use tools before finalizing.
    2. Start with list_repo_files.
    3. Read at least one source file related to the issue.
    4. Read at least one test file if tests are available.
    5. relevant_files may include source files, callers, tests, and docs.
    6. root_cause must identify the most direct cause of the bug.
    7. Do not blame a caller file if a lower-level function violates its contract.
    8. Your final answer must be valid JSON only.
    9. Use double quotes for all JSON keys and string values.
    10. Do not use Python dict syntax with single quotes.
    11. Do not wrap JSON in markdown fences.

    Final JSON schema:
    {
      "issue_type": "bug_fix | feature_request | refactor | test_request | documentation | unknown",
      "root_cause": "string",
      "relevant_files": ["path"],
      "evidence": ["file path + observed behavior"],
      "reasoning_summary": "string"
    }
    """
).strip()


def run_repo_navigation(
    repo_path: str,
    issue: str,
    code_files: list[str],
) -> RepoNavigationResult:
    tools = make_repo_tools(repo_path=repo_path, code_files=code_files)

    agent = create_repopilot_agent(
        agent_name="repo_navigator_agent",
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    user_prompt = dedent(
        f"""
        Investigate this repository issue.

        Issue:
        {issue}

        Scanned files:
        {chr(10).join(code_files)}

        You must call tools to inspect the repository before finalizing.

        Required tool behavior:
        - Call list_repo_files.
        - Read the most relevant source file.
        - Read the most relevant test file if present.

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

    return parse_agent_result(result, RepoNavigationResult)