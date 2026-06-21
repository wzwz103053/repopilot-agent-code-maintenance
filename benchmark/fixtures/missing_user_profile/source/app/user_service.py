USERS = {
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
