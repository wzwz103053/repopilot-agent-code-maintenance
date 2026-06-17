from __future__ import annotations

import re

from repopilot_agent.schemas.issue_router import (
    IssueRoute,
    IssueRouteCandidate,
    IssueRouteResult,
)


ROUTE_KEYWORDS: dict[IssueRoute, list[tuple[str, float]]] = {
    "bug_fix": [
        ("crash", 5.0),
        ("crashes", 5.0),
        ("bug", 5.0),
        ("fix", 4.0),
        ("error", 4.0),
        ("exception", 4.0),
        ("traceback", 4.0),
        ("fail", 4.0),
        ("fails", 4.0),
        ("failure", 4.0),
        ("broken", 4.0),
        ("does not work", 4.0),
        ("not exist", 3.5),
        ("none", 3.0),
        ("null", 3.0),
        ("missing", 3.0),
        ("incorrect", 3.0),
        ("wrong", 3.0),
    ],
    "test_generation": [
        ("add test", 6.0),
        ("write test", 6.0),
        ("generate test", 6.0),
        ("unit test", 5.0),
        ("pytest", 5.0),
        ("test coverage", 5.0),
        ("coverage", 4.0),
        ("regression test", 5.0),
        ("测试", 5.0),
        ("单元测试", 6.0),
    ],
    "refactor": [
        ("refactor", 6.0),
        ("clean up", 5.0),
        ("cleanup", 5.0),
        ("simplify", 4.0),
        ("rename", 4.0),
        ("restructure", 5.0),
        ("optimize", 4.0),
        ("improve structure", 5.0),
        ("重构", 6.0),
        ("优化结构", 5.0),
    ],
    "docs_update": [
        ("readme", 6.0),
        ("documentation", 6.0),
        ("docs", 5.0),
        ("document", 5.0),
        ("setup instructions", 5.0),
        ("usage", 4.0),
        ("guide", 4.0),
        ("说明文档", 6.0),
        ("文档", 5.0),
        ("使用说明", 5.0),
    ],
    "security_review": [
        ("security", 6.0),
        ("vulnerability", 6.0),
        ("unsafe", 5.0),
        ("injection", 5.0),
        ("prompt injection", 6.0),
        ("secret", 5.0),
        ("api key", 5.0),
        ("permission", 4.0),
        ("auth", 4.0),
        ("audit", 5.0),
        ("安全", 6.0),
        ("漏洞", 6.0),
        ("注入", 5.0),
    ],
    "unknown": [],
}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _contains_word_or_phrase(text: str, phrase: str) -> bool:
    phrase = phrase.lower().strip()

    if " " in phrase:
        return phrase in text

    # For English identifiers/words, avoid accidental substring matches.
    if re.fullmatch(r"[a-z0-9_]+", phrase):
        return re.search(rf"\b{re.escape(phrase)}\b", text) is not None

    # For Chinese or mixed text, substring matching is fine.
    return phrase in text


def _score_route(text: str, route: IssueRoute) -> IssueRouteCandidate:
    reasons: list[str] = []
    score = 0.0

    for keyword, weight in ROUTE_KEYWORDS[route]:
        if _contains_word_or_phrase(text, keyword):
            score += weight
            reasons.append(f"matched '{keyword}' (+{weight})")

    return IssueRouteCandidate(
        route=route,
        score=score,
        reasons=reasons,
    )


def _apply_tie_breakers(
    text: str,
    candidates: list[IssueRouteCandidate],
) -> list[IssueRouteCandidate]:
    """
    Apply simple deterministic tie-breakers.

    Example:
    - "test fails" is more likely bug_fix than test_generation.
    - "add tests" is test_generation.
    """
    by_route = {candidate.route: candidate for candidate in candidates}

    bug = by_route["bug_fix"]
    tests = by_route["test_generation"]
    docs = by_route["docs_update"]

    if any(phrase in text for phrase in ["test fails", "tests fail", "failing test"]):
        bug.score += 3.0
        bug.reasons.append("tie-breaker: failing tests indicate bug_fix (+3.0)")

    if any(phrase in text for phrase in ["add test", "write test", "generate test"]):
        tests.score += 3.0
        tests.reasons.append("tie-breaker: explicit request to add tests (+3.0)")

    if any(phrase in text for phrase in ["update readme", "readme", "docs only"]):
        docs.score += 3.0
        docs.reasons.append("tie-breaker: documentation-only signal (+3.0)")

    return candidates


def classify_issue_route(
    *,
    issue: str,
    code_files: list[str] | None = None,
    repo_summary: str = "",
) -> IssueRouteResult:
    """
    Deterministically classify an issue into a RepoPilot route.

    Important V18 fix:
    Route classification should be based primarily on the user's issue text.

    We intentionally do NOT score README.md or other repository filenames,
    because that can cause a bug report to be misclassified as docs_update
    simply because the repository contains README.md.
    """
    issue_text = _normalize(issue)

    candidates = [
        _score_route(issue_text, "bug_fix"),
        _score_route(issue_text, "test_generation"),
        _score_route(issue_text, "refactor"),
        _score_route(issue_text, "docs_update"),
        _score_route(issue_text, "security_review"),
    ]

    candidates = _apply_tie_breakers(issue_text, candidates)

    candidates.sort(key=lambda item: item.score, reverse=True)

    best = candidates[0]

    if best.score <= 0:
        unknown = IssueRouteCandidate(
            route="unknown",
            score=0.0,
            reasons=["no route keywords matched in the issue text"],
        )

        return IssueRouteResult(
            route="unknown",
            reason="No route-specific keywords matched the issue text.",
            confidence=0.0,
            candidates=candidates + [unknown],
        )

    total_score = sum(candidate.score for candidate in candidates if candidate.score > 0)
    confidence = best.score / total_score if total_score else 0.0

    reason = (
        f"Classified as {best.route} based on the user issue because "
        + "; ".join(best.reasons[:5])
    )

    return IssueRouteResult(
        route=best.route,
        reason=reason,
        confidence=round(confidence, 3),
        candidates=candidates,
    )