import json
from pathlib import Path

import requests
from dotenv import dotenv_values


class TokenError(Exception):
    pass


def login(login_url: str, user: str, password: str):
    message = "Login successful!"
    success = False

    try:
        login_response = requests.post(
            f"{login_url}", data={"username": user, "password": password}
        )
        # check status code/message on return then exit
        if login_response.ok:
            tokens = json.loads(login_response.text)
            saveTokens(tokens)
            success = True
        else:
            message = (
                f"Failed to login: {login_response.status_code}\n"
                f"\tResponse: {login_response.text}"
            )
    except requests.ConnectionError:
        message = f"Unable to connect to {login_url}"
    except requests.Timeout:
        message = "Timeout occurred waiting for login"

    return success, message


def saveTokens(tokens):
    if not tokens or len(tokens) == 0:
        raise ValueError("No tokens to save")

    functionaryDir = Path.home() / ".functionary"
    if not functionaryDir.exists():
        functionaryDir.mkdir()

    tokensFile = functionaryDir / "tokens"
    with tokensFile.open("wt"):
        tokensFile.write_text(f"token={tokens['token']}\n")


def getToken():
    tokensFile = Path.home() / ".functionary" / "tokens"

    config = {
        **dotenv_values(str(tokensFile)),
    }

    return config["token"]
