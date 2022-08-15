import json
from pathlib import Path

import requests
from dotenv import dotenv_values


class token_error(Exception):
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
            save_tokens(tokens)
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


def save_tokens(tokens):
    if not tokens or len(tokens) == 0:
        raise ValueError("No tokens to save")

    functionary_dir = Path.home() / ".functionary"
    if not functionary_dir.exists():
        functionary_dir.mkdir()

    config_file = functionary_dir / "config"
    with config_file.open("wt"):
        config_file.write_text(f"token={tokens['token']}\n")


def get_token():
    config_file = Path.home() / ".functionary" / "config"
    config = {
        **dotenv_values(str(config_file)),
    }
    return config["token"]
