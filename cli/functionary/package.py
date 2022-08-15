import os
import pathlib
import shutil
import tarfile

import click
import requests
import yaml

from .login import get_host, host_error
from .tokens import get_token, token_error


def create_languages() -> list[str]:
    spec = pathlib.Path(__file__).parent.resolve() / "templates"
    return [str(loc.name) for loc in spec.glob("*")]


def generateYaml(output_dir: str, name: str, language: str):
    metadata = {
        "name": name,
        "version": "1.0",
        "x-language": language,
    }

    path = pathlib.Path(output_dir).resolve() / name / f"{name}.yaml"
    with path.open(mode="w"):
        path.write_text(yaml.dump(metadata))


def get_environment_id():
    environment_id = os.environ.get("FUNCTIONARY_ENVIRONMENT")
    return environment_id


@click.group("package")
@click.pass_context
def package_cmd(ctx):
    pass


@package_cmd.command("create")
@click.option(
    "--language",
    "-l",
    type=click.Choice(create_languages(), case_sensitive=False),
    default="python",
)
@click.option("--output-directory", "-o", type=click.Path(exists=True), default=".")
@click.argument("name", type=str)
@click.pass_context
def create_cmd(ctx, language, name, output_directory):
    """
    Generate a function.

    Create an example function in the specified language.
    """
    click.echo()
    click.echo(f"Generating {language} function named {name}")
    dir = pathlib.Path(output_directory) / name
    if not dir.exists():
        dir.mkdir()

    basepath = pathlib.Path(__file__).parent.resolve() / "templates" / language

    shutil.copytree(str(basepath), str(dir), dirs_exist_ok=True)
    generateYaml(output_directory, name, language)


@package_cmd.command()
@click.argument("path", type=click.Path(exists=True))
@click.pass_context
def publish(ctx, path):
    """
    Create an archive from the project and publish to the build server.

    This will create an archive of the files at the given path and
    then publish them to the build server for image creation.
    Use the -t option to specify a token or set the FUNCTIONARY_TOKEN
    environment variable after logging in to Functionary.
    """
    try:
        token = get_token()
    except token_error as t:
        click.secho(str(t), err=True, fg="red")
        click.echo("Error getting token, try login again")
        ctx.exit(2)

    try:
        host = get_host()
    except host_error as h:
        click.secho(str(h), err=True, fg="red")
        click.echo("Error finding host name, try login again.")
        ctx.exit(2)

    full_path = pathlib.Path(path).resolve()
    tarfile_name = full_path.joinpath(f"{full_path.name}.tar.gz")
    with tarfile.open(str(tarfile_name), "w:gz") as tar:
        tar.add(str(full_path), arcname="")

    click.echo(f"Publishing {str(tarfile_name)} package to {host}")

    # publish should http the tar to a server, wait for return
    upload_file = open(tarfile_name, "rb")
    upload_response = None
    environment_id = get_environment_id()
    headers = {
        "Authorization": f"Token {token}",
        "X-Environment-ID": f"{environment_id}",
    }
    publish_url = host + "/api/v1/publish"
    try:
        upload_response = requests.post(
            publish_url, headers=headers, files={"package_contents": upload_file}
        )
    except requests.ConnectionError:
        click.echo(f"Unable to connect to {host}")
        ctx.exit(2)
    except requests.Timeout:
        click.echo("Timeout occurred waiting for build")
        ctx.exit(2)

    # check status code/message on return then exit
    if upload_response.ok:
        click.echo("Build succeeded")
    else:
        click.echo(
            f"Failed to build image: {upload_response.status_code}\n"
            f"\tResponse: {upload_response.text}"
        )
        if upload_response.status_code == 401:
            click.echo("\n\nTry log in again.")
        ctx.exit(1)
