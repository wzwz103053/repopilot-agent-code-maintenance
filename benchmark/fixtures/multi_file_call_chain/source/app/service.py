from app.repository import find_item


def get_display_name(item_id: str) -> str:
    item = find_item(item_id)
    return item["name"]
