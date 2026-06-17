from textwrap import dedent

from repopilot_agent.agents.agent_factory import create_repopilot_agent

from repopilot_agent.agents.base import get_llm, parse_agent_result
from repopilot_agent.schemas.patch import PatchProposal
from repopilot_agent.tools.repo_tools import make_repo_tools


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot Patch Writer Agent.

    Your responsibility:
    Generate a minimal unified diff patch based on the investigation result and patch plan.

    You must not directly modify files.
    You only propose a patch.

    Available tools:
    - list_repo_files: inspect repository structure
    - search_repo_code: search for symbols, functions, errors
    - read_repo_file: read repository file contents

    Patch writing rules:
    1. You must read the file that you plan to modify before generating the patch.
    2. Generate the smallest safe patch that fixes the root cause.
    3. Do not modify files that are not listed in files_to_modify.
    4. Do not modify tests unless files_to_modify explicitly includes test files.
    5. Preserve existing behavior for valid inputs.
    6. The patch must be a unified diff.
    7. Use file headers like:
       --- a/app/file.py
       +++ b/app/file.py
    8. Include at least one hunk header starting with @@.
    9. Do not include markdown fences inside the diff string.
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


def run_patch_writer(
    repo_path: str,
    issue: str,
    code_files: list[str],
    root_cause: str,
    relevant_files: list[str],
    files_to_modify: list[str],
    plan_steps: list[str],
    safety_notes: list[str],
) -> PatchProposal:
    tools = make_repo_tools(repo_path=repo_path, code_files=code_files)

    agent = create_repopilot_agent(
        agent_name="patch_writer_agent",
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    user_prompt = dedent(
        f"""
        Generate a minimal patch proposal for this issue.

        Issue:
        {issue}

        Root cause:
        {root_cause}

        Relevant files:
        {chr(10).join(f"- {file}" for file in relevant_files)}

        Files allowed to modify:
        {chr(10).join(f"- {file}" for file in files_to_modify)}

        Plan steps:
        {chr(10).join(f"{index}. {step}" for index, step in enumerate(plan_steps, start=1))}

        Safety notes:
        {chr(10).join(f"- {note}" for note in safety_notes)}

        Scanned files:
        {chr(10).join(code_files)}

        Required behavior:
        - Read every file in files_allowed_to_modify before writing the patch.
        - Generate a unified diff only for files listed in files_allowed_to_modify.
        - Make the patch minimal.
        - Return valid JSON only.
        - The JSON must include: diff, modified_files, explanation, risk_level, safety_notes.
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