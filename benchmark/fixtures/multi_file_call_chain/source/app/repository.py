ITEMS = {
    "i1": {"id": "i1", "name": "Keyboard"},
}


def find_item(item_id: str) -> dict | None:
    return ITEMS.get(item_id)
