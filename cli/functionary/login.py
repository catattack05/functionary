from pathlib import Path

import click

from .config import save_config_value
from .tokens import login


@click.command("login")
@click.option("--user", "-u", prompt=True)
@click.password_option(confirmation_prompt=False)
@click.argument("host", type=str)
@click.pass_context
def login_cmd(ctx, user, password, host):
    """
    Login to Functionary.

    Set the output of this command to the FUNCTIONARY_TOKEN environment variable
    for other functionary commands to use to communicate with the server.
    """
    login_url = f"{host}/api/v1/api-token-auth"
    # try to login, click will raise error from inside login if something goes wrong
    login(login_url, user, password)
    click.echo("Login successful!")
    save_config_value("host", host)
