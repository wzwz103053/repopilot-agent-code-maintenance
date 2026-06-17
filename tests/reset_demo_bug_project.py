from pathlib import Path


ROOT = Path("playground_repo/demo_bug_project").resolve()

APP_DIR = ROOT / "app"
TESTS_DIR = ROOT / "tests"

USER_SERVICE = APP_DIR / "user_service.py"
PROFILE = APP_DIR / "profile.py"
APP_INIT = APP_DIR / "__init__.py"

TEST_PROFILE = TESTS_DIR / "test_profile.py"
README = ROOT / "README.md"


# 关键：先创建父目录，否则 write_text 会因为目录不存在而失败
APP_DIR.mkdir(parents=True, exist_ok=True)
TESTS_DIR.mkdir(parents=True, exist_ok=True)

APP_INIT.write_text("", encoding="utf-8")

USER_SERVICE.write_text(
    '''USERS = {
    "u1": {
        "id": "u1",
        "name": "Alice",
        "email": "alice@example.com",
    }
}


def get_user(user_id: str) -> dict | None:
    return USERS.get(user_id)


def get_user_profile(user_id: str) -> dict:
    user = get_user(user_id)
    return {
        "display_name": user["name"],
        "email": user["email"],
    }
''',
    encoding="utf-8",
)

PROFILE.write_text(
    '''from app.user_service import get_user_profile


def render_profile_page(user_id: str) -> str:
    profile = get_user_profile(user_id)
    return f"Profile: {profile['display_name']} <{profile['email']}>"
''',
    encoding="utf-8",
)

TEST_PROFILE.write_text(
    '''from app.profile import render_profile_page


def test_existing_user_profile():
    html = render_profile_page("u1")
    assert "Alice" in html


def test_missing_user_profile_should_not_crash():
    html = render_profile_page("missing")
    assert "Unknown user" in html
''',
    encoding="utf-8",
)

README.write_text(
    '''# Demo Bug Project

A tiny Python project used to test RepoPilot.

Known issue:
When a missing user opens the profile page, the page crashes instead of showing a safe fallback.
''',
    encoding="utf-8",
)

print("Demo bug project reset to original broken state.")
print(ROOT)