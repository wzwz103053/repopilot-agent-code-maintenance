import ast
import json
import re
from typing import TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from repopilot_agent.config import load_config


T = TypeVar("T", bound=BaseModel)


def get_llm() -> ChatOpenAI:
    """
    创建统一 ChatOpenAI-compatible 模型实例。

    当前支持 DashScope / OpenAI-compatible 平台。
    """
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


def extract_json_from_text(text: str) -> dict:
    """
    从模型最终输出中提取结构化数据。

    兼容：
    1. 标准 JSON
    2. Markdown JSON
    3. Python dict 风格单引号
    """
    content = text.strip()

    print("\n[agent raw final output]")
    print(content)
    print("[end agent raw final output]\n")

    if content.startswith("```"):
        content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"^```\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, flags=re.DOTALL)

    if not match:
        raise ValueError(f"No JSON object found in model output:\n{text}")

    object_text = match.group(0)

    try:
        return json.loads(object_text)
    except json.JSONDecodeError:
        pass

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
    从 create_agent 返回结果中找到最后一条 AI 文本消息。
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


def parse_agent_result(agent_result: dict, schema: type[T]) -> T:
    """
    把 Agent 输出解析成 Pydantic schema。
    """
    final_text = get_last_ai_text(agent_result)
    data = extract_json_from_text(final_text)

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(
            f"Model returned structured data, but it does not match {schema.__name__}.\n"
            f"Raw data:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
            f"Validation error:\n{exc}"
        ) from exc