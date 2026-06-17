from __future__ import annotations

import os

from repopilot_agent.state import RepoPilotState
from repopilot_agent.tools.code_index_tools import (
    build_code_index,
    build_retrieval_queries,
    format_retrieval_context,
    retrieve_code_chunks,
    retrieved_files_from_chunks,
    summarize_retrieval,
    unique_keep_order,
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def build_code_index_node(state: RepoPilotState) -> dict:
    print("[subgraph node] build_code_index")

    if not _env_bool("REPOPILOT_ENABLE_RETRIEVAL", True):
        return {
            "retrieval_status": "disabled",
            "code_chunks": [],
            "retrieval_summary": "Retrieval is disabled.",
        }

    chunk_size = _env_int("REPOPILOT_RETRIEVAL_CHUNK_SIZE", 80)
    overlap = _env_int("REPOPILOT_RETRIEVAL_CHUNK_OVERLAP", 20)

    chunks = build_code_index(
        repo_path=state["repo_path"],
        code_files=state.get("code_files", []),
        chunk_size=chunk_size,
        overlap=overlap,
    )

    return {
        "retrieval_status": "indexed",
        "code_chunks": chunks,
        "retrieval_summary": f"Indexed {len(chunks)} code chunks.",
    }


def build_retrieval_queries_node(state: RepoPilotState) -> dict:
    print("[subgraph node] build_retrieval_queries")

    if state.get("retrieval_status") == "disabled":
        return {
            "retrieval_queries": [],
        }

    queries = build_retrieval_queries(
        issue=state["issue"],
        repo_summary=state.get("repo_summary", ""),
        file_tree=state.get("file_tree", ""),
    )

    return {
        "retrieval_queries": queries,
    }


def retrieve_code_context_node(state: RepoPilotState) -> dict:
    print("[subgraph node] retrieve_code_context")

    if state.get("retrieval_status") == "disabled":
        return {
            "retrieved_chunks": [],
            "retrieved_files": [],
            "retrieval_context": "",
            "retrieval_summary": "Retrieval is disabled.",
        }

    top_k = _env_int("REPOPILOT_RETRIEVAL_TOP_K", 6)
    max_context_chars = _env_int("REPOPILOT_RETRIEVAL_MAX_CONTEXT_CHARS", 6000)

    chunks = state.get("code_chunks", [])
    queries = state.get("retrieval_queries", [])

    retrieved_chunks = retrieve_code_chunks(
        chunks=chunks,
        queries=queries,
        top_k=top_k,
    )

    retrieved_files = retrieved_files_from_chunks(retrieved_chunks)
    retrieval_context = format_retrieval_context(
        retrieved_chunks=retrieved_chunks,
        max_chars=max_context_chars,
    )

    retrieval_summary = summarize_retrieval(
        chunks=chunks,
        retrieved_chunks=retrieved_chunks,
        retrieved_files=retrieved_files,
    )

    # Re-rank code_files so Repo Navigator sees retrieved files first.
    existing_code_files = state.get("code_files", [])
    reranked_code_files = unique_keep_order(
        retrieved_files
        + [
            file
            for file in existing_code_files
            if file not in set(retrieved_files)
        ]
    )

    return {
        "retrieval_status": "retrieved",
        "retrieved_chunks": retrieved_chunks,
        "retrieved_files": retrieved_files,
        "retrieval_context": retrieval_context,
        "retrieval_summary": retrieval_summary,
        "code_files": reranked_code_files,
    }