from textwrap import dedent

from repopilot_agent.agents.agent_factory import create_repopilot_agent

from repopilot_agent.agents.base import get_llm, parse_agent_result
from repopilot_agent.schemas.patch import PatchProposal
from repopilot_agent.tools.repo_tools import make_repo_tools


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot Repair Agent.

    Your responsibility:
    Generate a repair patch after tests fail.

    You must use:
    - the original issue
    - the previous patch
    - the test failure analysis
    - the current repository files

    You must not directly modify files.
    You only propose a new unified diff patch.

    Available tools:
    - list_repo_files: inspect repository structure
    - search_repo_code: search for symbols, functions, errors
    - read_repo_file: read repository file contents

    Repair rules:
    1. Read the affected files before proposing a repair patch.
    2. Use the test failure analysis as the primary feedback.
    3. Keep the repair patch minimal.
    4. Do not rewrite unrelated code.
    5. Do not modify tests unless the failure analysis says the tests are wrong.
    6. Preserve behavior that was already working.
    7. The patch must be a unified diff.
    8. Use file headers like:
       --- a/app/file.py
       +++ b/app/file.py
    9. Include at least one hunk header starting with @@.
    10. Your final answer must be valid JSON only.
    11. Use double quotes for all JSON keys and string values.
    12. Do not use Python dict syntax with single quotes.
    13. Do not wrap JSON in markdown fences.

    Final JSON schema:
    {
      "diff": "unified diff string",
      "modified_files": ["path"],
      "explanation": "string",
      "risk_level": "low | medium | high",
      "safety_notes": ["note"]
    }
    """
).strip()


def run_repair_agent(
    repo_path: str,
    issue: str,
    code_files: list[str],
    previous_patch: str,
    modified_files: list[str],
    failure_type: str,
    failure_analysis: str,
    failure_evidence: list[str],
    affected_files: list[str],
    test_output: str,
) -> PatchProposal:
    tools = make_repo_tools(repo_path=repo_path, code_files=code_files)

    agent = create_repopilot_agent(
        agent_name="test_analyst_agent",
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    user_prompt = dedent(
        f"""
        Generate a repair patch for this failed code fix.

        Original issue:
        {issue}

        Previous patch:
        {previous_patch}

        Previously modified files:
        {chr(10).join(f"- {file}" for file in modified_files)}

        Failure type:
        {failure_type}

        Failure analysis:
        {failure_analysis}

        Failure evidence:
        {chr(10).join(f"- {item}" for item in failure_evidence)}

        Affected files:
        {chr(10).join(f"- {file}" for file in affected_files)}

        Test output:
        {test_output}

        Scanned files:
        {chr(10).join(code_files)}

        Required behavior:
        - Read the affected files before finalizing.
        - Generate a minimal unified diff patch.
        - Return valid JSON only.
        - Use double quotes for all JSON keys and string values.
        - Do not include markdown fences.
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

    return parse_agent_result(result, PatchProposal)