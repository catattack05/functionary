from pathlib import Path

import click
from dotenv import dotenv_values

from .tokens import login


class host_error(Exception):
    pass


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
    success, message = login(login_url, user, password)

    # check status code/message on return then exit
    if success:
        click.echo("Login successful!")
        # save host for future commands on success
        save_host(host)

    else:
        click.secho(
            message,
            err=True,
            fg="red",
        )
        ctx.exit(1)


def save_host(host):
    functionary_dir = Path.home() / ".functionary"
    if not functionary_dir.exists():
        functionary_dir.mkdir()

    config_file = functionary_dir / "config"
    with config_file.open("a") as f:
        f.write(f"host={host}\n")


def get_host():
    config_file = Path.home() / ".functionary" / "config"

    config = {
        **dotenv_values(str(config_file)),
    }

    return config["host"]
