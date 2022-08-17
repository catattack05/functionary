import json

import click
import requests

from .config import get_config_value, save_config_value


def get_environment_list():
    """
    Helper function to get the environment list from host

    Args:
        None

    Returns:
        None

    Raises:
        ClickException if bad get request
    """
    token = get_config_value("token")
    teams_url = get_config_value("host") + "/api/v1/teams"
    header = {"Authorization": f"Token {token}"}
    response = requests.get(teams_url, headers=header)

    if response.ok:
        data = json.loads(response.text).get("results")

        env_list = []
        for team in data:
            for env_set in team.get("environments"):
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
    pass


@environment_cmd.command()
@click.pass_context
def set(ctx):
    """
    Command to set the environment id based on user input

    Args:
        Ctx: The click context

    Returns:
        None

    Raises:
        ClickException if bad environment number
    """
    env_list = get_environment_list()
    index = 1
    click.echo("Available Environments:")
    for item in env_list:
        click.echo(f"    {index}) {item.get('name')}")
        index += 1
    user_choice = click.prompt("Select environment", type=int)
    try:
        value = env_list[user_choice - 1]
    except IndexError:
        raise click.ClickException("Environment number chosen is not valid")
    click.echo(f"Active environment is now {value.get('name')}")
    save_config_value("current_environment", json.dumps(value))


@environment_cmd.command()
@click.pass_context
def list(ctx):
    """
    Command to list all possible environments

    Args:
        Ctx: The click context

    Returns:
        None
    """
    env_list = get_environment_list()
    current_env_id = json.loads(get_config_value("current_environment")).get("id")
    for item in env_list:
        name = item.get("name")
        active = "  "
        if current_env_id == item.get("id"):
            active = "* "

        click.echo(f"{active}{name}")
