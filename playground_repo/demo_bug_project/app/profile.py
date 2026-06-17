from app.user_service import get_user_profile


def render_profile_page(user_id: str) -> str:
    profile = get_user_profile(user_id)
    return f"Profile: {profile['display_name']} <{profile['email']}>"
