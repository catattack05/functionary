import json

import click
import requests


def login(login_url, user: str, password: str):
    try:
        login_response = requests.post(
            f"{login_url}", data={"username": user, "password": password}
        )
        # check status code/message on return then exit
        if login_response.ok:
            token = json.loads(login_response.text).get("token")
            return token
        else:
            raise click.ClickException(
                f"Failed to login: {login_response.status_code}\n"
                f"Response: {login_response.text}"
            )
    except requests.ConnectionError:
        raise click.ClickException(f"Unable to connect to {login_url}.")
    except requests.Timeout:
        raise click.ClickException("Timeout occurred waiting for login")
