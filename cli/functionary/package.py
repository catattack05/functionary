import pathlib
import shutil
import tarfile

import click
import yaml

from .client import post
from .config import get_config_value


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
    host = get_config_value("host")

    full_path = pathlib.Path(path).resolve()
    tarfile_name = full_path.joinpath(f"{full_path.name}.tar.gz")
    with tarfile.open(str(tarfile_name), "w:gz") as tar:
        tar.add(str(full_path), arcname="")

    upload_file = open(tarfile_name, "rb")
    click.echo(f"Publishing {str(tarfile_name)} package to {host}")

    post("publish", upload_file)

    click.echo("Publish succeded")

