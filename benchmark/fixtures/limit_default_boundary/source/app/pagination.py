def top_items(items: list[str], limit: int | None = None) -> list[str]:
    if limit is None:
        return []

    return items[:limit]
