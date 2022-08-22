from .client import post


def login(user: str, password: str):
    login_response = post("api-token-auth", {"username": user, "password": password})
    token = login_response.get("token")
    return token
