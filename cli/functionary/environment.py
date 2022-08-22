import json

import click
import requests

from .config import get_config_value, save_config_value


def _get_environment_list():
    """
    Helper function to get the environment list from host
    """
    token = get_config_value("token")
    teams_url = get_config_value("host") + "/api/v1/teams"
    header = {"Authorization": f"Token {token}"}
    try:
        response = requests.get(teams_url, headers=header)
    except requests.ConnectionError:
        raise click.ClickException("Could not connect to host")
    except requests.Timeout:
        raise click.ClickException("Timeout occured while trying to connect to host")

    if response.ok:
        data = json.loads(response.text).get("results")

        env_list = []
        for team in data:
            for env_set in team.get("environments"):
                env_set["team"] = team.get("name")
                env_list.append(env_set)
        return env_list
    else:
        raise click.ClickException(
            f"Failed to get environment list: {response.status_code}\n"
            f"Response: {response.text}"
        )


@click.group("environment")
@click.pass_context
def environment_cmd(ctx):
    """
    List or set environments
    """
    pass


@environment_cmd.command()
@click.pass_context
def set(ctx):
    """
    Set the active environment
    """
    env_list = _get_environment_list()
    index = 1
    click.echo("Available Environments:")
    for item in env_list:
        click.echo(f"    {index}) {item.get('team')} - {item.get('name')}")
        index += 1
    user_choice = click.prompt("Select environment", type=int)
    try:
        value = env_list[user_choice - 1]
    except IndexError:
        raise click.ClickException("Environment number chosen is not valid")
    click.echo(
        f"Active environment is now {value.get('name')} from {value.get('team')}"
    )
    save_config_value("current_environment_id", value.get("id"))


@environment_cmd.command()
@click.pass_context
def list(ctx):
    """
    List all available environments
    """
    env_list = _get_environment_list()
    try:
        current_env_id = get_config_value("current_environment_id")
    except click.ClickException:
        current_env_id = None
    for item in env_list:
        name = item.get("name")
        team = item.get("team")
        active = "  "
        if current_env_id == item.get("id"):
            active = "* "

        click.echo(f"{active}{team} - {name}")
