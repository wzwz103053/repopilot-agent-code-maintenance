from app.api import get_item_label


def test_existing_item_label():
    assert get_item_label("i1") == "Item: Keyboard"


def test_missing_item_label():
    assert get_item_label("missing") == "Item: Unknown item"
