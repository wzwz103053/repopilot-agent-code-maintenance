import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(override=True)


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_name: str
    api_key: str
    base_url: str
    temperature: float
    max_tokens: int
    timeout: float
    max_retries: int


@dataclass(frozen=True)
class RepoPilotConfig:
    model: ModelConfig
    default_max_repair_attempts: int
    default_auto_approve: bool


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> RepoPilotConfig:
    """
    统一读取 RepoPilot 配置。

    当前默认使用 DashScope / 阿里云百炼 OpenAI-compatible 接口。
    后面如果要换 DeepSeek、OpenRouter、OpenAI 官方，只需要改这里。
    """
    provider = os.getenv("REPOPILOT_MODEL_PROVIDER", "dashscope")

    if provider == "dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        base_url = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        model_name = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
        temperature = float(os.getenv("DASHSCOPE_TEMPERATURE", "0"))
        max_tokens = int(os.getenv("DASHSCOPE_MAX_TOKENS", "3000"))
        timeout = float(os.getenv("DASHSCOPE_TIMEOUT_SECONDS", "120"))
        max_retries = int(os.getenv("DASHSCOPE_MAX_RETRIES", "1"))

        if not api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY is missing. Please set it in your .env file."
            )

        model_config = ModelConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
        )

    else:
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model_name = os.getenv("REPOPILOT_MODEL", "gpt-4o-mini")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Please set it in your .env file."
            )

        model_config = ModelConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=float(os.getenv("REPOPILOT_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("REPOPILOT_MAX_TOKENS", "3000")),
            timeout=float(os.getenv("REPOPILOT_TIMEOUT_SECONDS", "120")),
            max_retries=int(os.getenv("REPOPILOT_MAX_RETRIES", "1")),
        )

    return RepoPilotConfig(
        model=model_config,
        default_max_repair_attempts=int(os.getenv("REPOPILOT_MAX_REPAIR_ATTEMPTS", "2")),
        default_auto_approve=_get_bool_env("REPOPILOT_AUTO_APPROVE", True),
    )