from app.profile import render_profile_page


def test_existing_user_profile():
    html = render_profile_page("u1")
    assert "Alice" in html


def test_missing_user_profile_should_not_crash():
    html = render_profile_page("missing")
    assert "Unknown user" in html
