import pytest

from app.pagination import top_items


def test_limit_omitted_returns_all_items():
    assert top_items(["a", "b", "c"]) == ["a", "b", "c"]


def test_negative_limit_is_rejected():
    with pytest.raises(ValueError):
        top_items(["a", "b"], limit=-1)
