from __future__ import annotations

import os
from typing import Any


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _safe_create_middleware(
    middleware_name: str,
    constructor: Any,
    *args: Any,
    **kwargs: Any,
) -> Any | None:
    """
    Create middleware safely.

    Different langchain versions may expose slightly different constructor
    signatures. RepoPilot should not crash just because one optional middleware
    is unavailable or incompatible.
    """
    try:
        return constructor(*args, **kwargs)
    except Exception as exc:
        print(
            f"[repopilot middleware] skipped {middleware_name}: {exc}",
            flush=True,
        )
        return None


def _load_pii_middlewares() -> list[Any]:
    """
    Load built-in PIIMiddleware when available.

    V11 already performs deterministic secret redaction for repository files.
    V12 adds LangChain-level PII middleware as an additional agent harness layer.
    """
    if not env_bool("REPOPILOT_ENABLE_PII_MIDDLEWARE", True):
        return []

    try:
        from langchain.agents.middleware import PIIMiddleware
    except Exception as exc:
        print(
            f"[repopilot middleware] PIIMiddleware unavailable: {exc}",
            flush=True,
        )
        return []

    strategy = os.getenv("REPOPILOT_PII_STRATEGY", "redact")
    apply_to_input = env_bool("REPOPILOT_PII_APPLY_TO_INPUT", True)
    apply_to_output = env_bool("REPOPILOT_PII_APPLY_TO_OUTPUT", True)

    pii_types = [
        item.strip()
        for item in os.getenv(
            "REPOPILOT_PII_TYPES",
            "email,ip_address,credit_card",
        ).split(",")
        if item.strip()
    ]

    middlewares: list[Any] = []

    for pii_type in pii_types:
        middleware = _safe_create_middleware(
            f"PIIMiddleware({pii_type})",
            PIIMiddleware,
            pii_type,
            strategy=strategy,
            apply_to_input=apply_to_input,
            apply_to_output=apply_to_output,
        )

        if middleware is not None:
            middlewares.append(middleware)

    return middlewares


def _load_hitl_middleware(agent_name: str) -> list[Any]:
    """
    Load HumanInTheLoopMiddleware when explicitly enabled.

    Important:
    RepoPilot already has graph-level human_review for patch proposal approval.
    This middleware is optional and is mainly used to demonstrate tool-call-level
    human review.

    Keep it disabled by default, otherwise read_repo_file/search_repo_code may
    interrupt during normal automated tests.
    """
    if not env_bool("REPOPILOT_ENABLE_HITL_MIDDLEWARE", False):
        return []

    try:
        from langchain.agents.middleware import HumanInTheLoopMiddleware
    except Exception as exc:
        print(
            f"[repopilot middleware] HumanInTheLoopMiddleware unavailable: {exc}",
            flush=True,
        )
        return []

    interrupt_on: dict[str, dict[str, list[str]]] = {}

    if env_bool("REPOPILOT_HITL_ON_READ_REPO_FILE", False):
        interrupt_on["read_repo_file"] = {
            "allowed_decisions": ["approve", "reject"]
        }

    if env_bool("REPOPILOT_HITL_ON_SEARCH_REPO_CODE", False):
        interrupt_on["search_repo_code"] = {
            "allowed_decisions": ["approve", "reject"]
        }

    if not interrupt_on:
        return []

    middleware = _safe_create_middleware(
        f"HumanInTheLoopMiddleware({agent_name})",
        HumanInTheLoopMiddleware,
        interrupt_on=interrupt_on,
    )

    return [middleware] if middleware is not None else []


def _load_summarization_middleware() -> list[Any]:
    """
    Optional summarization middleware.

    Keep disabled by default because some provider/model combinations may not
    support the exact constructor signature. This is mainly prepared for larger
    repositories where tool results can make agent messages very long.
    """
    if not env_bool("REPOPILOT_ENABLE_SUMMARIZATION_MIDDLEWARE", False):
        return []

    try:
        from langchain.agents.middleware import SummarizationMiddleware
    except Exception as exc:
        print(
            f"[repopilot middleware] SummarizationMiddleware unavailable: {exc}",
            flush=True,
        )
        return []

    max_tokens_before_summary = env_int(
        "REPOPILOT_SUMMARY_MAX_TOKENS_BEFORE_SUMMARY",
        6000,
    )

    messages_to_keep = env_int(
        "REPOPILOT_SUMMARY_MESSAGES_TO_KEEP",
        6,
    )

    middleware = _safe_create_middleware(
        "SummarizationMiddleware",
        SummarizationMiddleware,
        max_tokens_before_summary=max_tokens_before_summary,
        messages_to_keep=messages_to_keep,
    )

    return [middleware] if middleware is not None else []


def build_repopilot_middleware(agent_name: str) -> list[Any]:
    """
    Build the middleware list for a RepoPilot agent.

    This is the central place to configure agent-level middleware.
    """
    if not env_bool("REPOPILOT_ENABLE_AGENT_MIDDLEWARE", True):
        return []

    middlewares: list[Any] = []

    middlewares.extend(_load_pii_middlewares())
    middlewares.extend(_load_hitl_middleware(agent_name))
    middlewares.extend(_load_summarization_middleware())

    if middlewares:
        print(
            f"[repopilot middleware] {agent_name}: loaded {len(middlewares)} middleware(s)",
            flush=True,
        )
    else:
        print(
            f"[repopilot middleware] {agent_name}: no middleware loaded",
            flush=True,
        )

    return middlewares