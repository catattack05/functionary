from .client import post


def login(user: str, password: str):
    login_response = post(
        "api-token-auth", data={"username": user, "password": password}
    )
    return login_response.get("token")
