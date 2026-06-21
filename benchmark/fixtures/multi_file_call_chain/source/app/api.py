from app.service import get_display_name


def get_item_label(item_id: str) -> str:
    return f"Item: {get_display_name(item_id)}"
