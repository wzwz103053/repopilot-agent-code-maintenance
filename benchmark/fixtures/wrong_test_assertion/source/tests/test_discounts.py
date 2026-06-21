from app.discounts import apply_discount


def test_ten_percent_discount():
    assert apply_discount(100, 0.10) == 95
