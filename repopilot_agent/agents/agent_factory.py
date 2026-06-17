from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

from repopilot_agent.agents.middleware import build_repopilot_middleware


def create_repopilot_agent(
    *,
    agent_name: str,
    model: Any,
    tools: list[Any],
    system_prompt: str,
    response_format: Any | None = None,
) -> Any:
    """
    Create a LangChain agent for RepoPilot.

    V12 purpose:
    - Give every agent a stable name.
    - Attach LangChain middleware in one central place.
    - Keep compatibility with provider/model versions that may not support every
      optional create_agent argument.
    """
    middleware = build_repopilot_middleware(agent_name)

    kwargs: dict[str, Any] = {
        "model": model,
        "tools": tools,
        "system_prompt": system_prompt,
    }

    if middleware:
        kwargs["middleware"] = middleware

    if response_format is not None:
        kwargs["response_format"] = response_format

    # Some versions support name=, some may not. Try it first for better traces.
    kwargs_with_name = dict(kwargs)
    kwargs_with_name["name"] = agent_name

    try:
        return create_agent(**kwargs_with_name)
    except TypeError as exc:
        print(
            f"[repopilot agent factory] create_agent name= unsupported for "
            f"{agent_name}, retrying without name: {exc}",
            flush=True,
        )

    try:
        return create_agent(**kwargs)
    except TypeError as exc:
        # If middleware is unsupported by the installed version, retry without it.
        if "middleware" in kwargs:
            print(
                f"[repopilot agent factory] middleware unsupported for "
                f"{agent_name}, retrying without middleware: {exc}",
                flush=True,
            )
            kwargs_without_middleware = dict(kwargs)
            kwargs_without_middleware.pop("middleware", None)
            return create_agent(**kwargs_without_middleware)

        raise