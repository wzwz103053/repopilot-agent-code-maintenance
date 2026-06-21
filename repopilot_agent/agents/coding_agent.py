import ast
import json
import re
from textwrap import dedent

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from repopilot_agent.config import load_config
from repopilot_agent.schemas.investigation import InvestigationResult
from repopilot_agent.tools.agent_tools import make_repo_tools


def get_llm() -> ChatOpenAI:
    config = load_config()
    model_config = config.model

    return ChatOpenAI(
        model=model_config.model_name,
        api_key=model_config.api_key,
        base_url=model_config.base_url,
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens,
        timeout=model_config.timeout,
        max_retries=model_config.max_retries,
    )


SYSTEM_PROMPT = dedent(
    """
    You are RepoPilot, a coding investigation agent.

    Your job is to investigate a repository issue by using tools.
    You must not guess without reading files.

    Available tools:
    - list_repo_files: inspect repository structure
    - search_repo_code: search for symbols, keywords, functions, or errors
    - read_repo_file: inspect file contents

    Investigation rules:
    1. You must inspect repository files before giving the final answer.
    2. You must distinguish relevant files from files to modify.
    3. relevant_files can include callers, source files, tests, and docs.
    4. files_to_modify must include only the minimal files that need code changes.
    5. Do not include a caller file in files_to_modify unless the caller itself contains the direct bug.
    6. Prefer fixing the function that violates its contract over adding defensive checks in every caller.
    7. Use tests to understand expected behavior, but do not modify tests unless the existing tests are wrong or incomplete.
    8. Do not propose optional hardening changes in files_to_modify.
    9. Do not propose broad rewrites.
    10. Your final answer must be valid JSON only.
    11. Use double quotes for all JSON keys and string values.
    12. Do not use Python dict syntax with single quotes.
    13. Do not wrap the JSON in markdown fences.

    For this repository style:
    - If a service function returns invalid data or crashes, prefer fixing the service function.
    - If a page/render function simply consumes the service result, do not modify it unless it has its own independent bug.

    Final JSON schema:
    {
      "issue_type": "bug_fix | feature_request | refactor | test_request | documentation | unknown",
      "root_cause": "string",
      "relevant_files": ["path"],
      "files_to_modify": ["path"],
      "plan_steps": ["step"],
      "risk_level": "low | medium | high",
      "evidence": ["file path + observed behavior"],
      "reasoning_summary": "string"
    }
    """
).strip()


def extract_json_from_text(text: str) -> dict:
    """
    从模型最终输出中提取结构化数据。

    兼容三种情况：
    1. 标准 JSON: {"issue_type": "bug_fix"}
    2. Markdown JSON: ```json ... ```
    3. Python dict 风格: {'issue_type': 'bug_fix'}
    """
    content = text.strip()

    print("\n[agent raw final output]")
    print(content)
    print("[end agent raw final output]\n")

    if content.startswith("```"):
        content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"^```\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    # 1. 先尝试标准 JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 2. 再尝试从文本里截取最外层 {...}
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output:\n{text}")

    object_text = match.group(0)

    try:
        return json.loads(object_text)
    except json.JSONDecodeError:
        pass

    # 3. 最后兼容 Python dict 风格，也就是单引号的 {'a': 'b'}
    try:
        data = ast.literal_eval(object_text)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(
            "Model output is neither valid JSON nor a valid Python dict-like object.\n"
            f"Raw output:\n{text}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Parsed model output is not a dictionary.\n"
            f"Raw output:\n{text}"
        )

    return data


def get_last_ai_text(agent_result: dict) -> str:
    """
    从 create_agent 的返回结果中找到最后一条 AI 文本消息。
    """
    messages = agent_result.get("messages", [])

    for message in reversed(messages):
        content = getattr(message, "content", None)

        if isinstance(content, str) and content.strip():
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))

            text = "\n".join(parts).strip()
            if text:
                return text

    raise RuntimeError("No final AI text message found in agent result.")


def run_coding_investigation(
    repo_path: str,
    issue: str,
    code_files: list[str],
) -> InvestigationResult:
    tools = make_repo_tools(repo_path=repo_path, code_files=code_files)

    # 注意：
    # 这里不使用 response_format=ToolStrategy(...)
    # 因为 DashScope thinking mode 可能不支持 tool_choice=required/object。
    # 我们保留 Agent 工具调用能力，然后让模型输出 JSON 文本，再由 Python 解析。
    agent = create_agent(
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
        At minimum, inspect the source file related to the issue and the test file that describes expected behavior.

        After investigation, return valid JSON only.
        Use double quotes for all JSON keys and string values.
        Do not use Python dict syntax with single quotes.
        Do not include markdown fences.
        The JSON must include all required fields, including evidence.
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

    final_text = get_last_ai_text(result)
    data = extract_json_from_text(final_text)

    try:
        return InvestigationResult.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(
            "Model returned JSON, but it does not match InvestigationResult schema.\n"
            f"Raw JSON:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
            f"Validation error:\n{exc}"
        ) from exc
