from __future__ import annotations

from pathlib import Path

from repopilot_agent.state import RepoPilotState


DOC_FILE_PRIORITY = [
    "README.md",
    "README.rst",
    "README.txt",
    "docs/README.md",
    "docs/index.md",
]


def _format_list(items: list[str]) -> str:
    if not items:
        return "- None"

    return "\n".join(f"- {item}" for item in items)


def _find_docs_targets(code_files: list[str]) -> list[str]:
    """
    Choose documentation files to update.

    V16 starts with a deterministic strategy:
    1. Prefer README files.
    2. Then docs/*.md.
    3. Then any markdown file.
    """
    normalized = [file.replace("\\", "/") for file in code_files]

    targets: list[str] = []

    for candidate in DOC_FILE_PRIORITY:
        if candidate in normalized:
            targets.append(candidate)

    if targets:
        return targets[:1]

    docs_md_files = [
        file
        for file in normalized
        if file.startswith("docs/") and Path(file).suffix.lower() == ".md"
    ]

    if docs_md_files:
        return docs_md_files[:1]

    markdown_files = [
        file
        for file in normalized
        if Path(file).suffix.lower() in {".md", ".rst", ".txt"}
    ]

    return markdown_files[:1]


def docs_target_node(state: RepoPilotState) -> dict:
    print("[subgraph node] docs_target_selector")

    code_files = state.get("code_files", [])
    docs_target_files = _find_docs_targets(code_files)

    if not docs_target_files:
        return {
            "docs_update_status": "blocked",
            "docs_target_files": [],
            "files_to_modify": [],
            "relevant_files": [],
            "evidence": [
                "No documentation file was found in the scanned repository."
            ],
            "docs_update_summary": "No documentation file was found.",
        }

    return {
        "docs_update_status": "target_selected",
        "docs_target_files": docs_target_files,
        "files_to_modify": docs_target_files,
        "relevant_files": docs_target_files,
        "evidence": [
            f"Selected documentation target: {docs_target_files[0]}",
            "The issue was routed as docs_update by issue_router.",
        ],
        "docs_update_summary": (
            f"Selected {docs_target_files[0]} as the documentation update target."
        ),
    }


def docs_plan_node(state: RepoPilotState) -> dict:
    print("[subgraph node] docs_plan_builder")

    issue = state["issue"]
    docs_target_files = state.get("docs_target_files", [])

    if not docs_target_files:
        return {
            "docs_update_status": "blocked",
            "plan": "Docs update cannot continue because no documentation target was found.",
            "plan_steps": [
                "Stop the docs update because no documentation target file exists."
            ],
            "risk_level": "low",
            "safety_notes": [
                "No patch should be generated because no docs target was found."
            ],
        }

    target = docs_target_files[0]

    plan_steps = [
        f"Open {target} and preserve existing useful content.",
        "Add or update a concise section that addresses the user's documentation request.",
        "Prefer minimal documentation changes over rewriting the entire file.",
        "Do not modify source code for a docs_update task.",
        "Do not modify tests for a docs_update task.",
    ]

    safety_notes = [
        "Documentation-only route: source code and tests should not be changed.",
        "Patch should be limited to the selected documentation file.",
        "Do not include secrets, API keys, or private local paths in documentation.",
    ]

    plan = f"""
Task type:
docs_update

User request:
{issue}

Documentation target files:
{_format_list(docs_target_files)}

Files to modify:
{_format_list(docs_target_files)}

Plan steps:
{_format_list(plan_steps)}

Risk level:
low

Safety notes:
{_format_list(safety_notes)}
""".strip()

    return {
        "docs_update_status": "planned",
        "issue_type": "docs_update",
        "root_cause": (
            "This is not a runtime bug. The issue was classified as a documentation "
            "update request."
        ),
        "files_to_modify": docs_target_files,
        "plan_steps": plan_steps,
        "risk_level": "low",
        "safety_notes": safety_notes,
        "plan": plan,
        "docs_update_summary": (
            f"Prepared a documentation update plan for {target}."
        ),
    }