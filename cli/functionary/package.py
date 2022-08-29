import pathlib
import shutil
import tarfile

import click
import yaml
from rich.console import Console
from rich.table import Table

from .client import get, post
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

    response = post("publish", files={"package_contents": upload_file})
    upload_file.close()
    id = response["id"]
    click.echo(f"Publish {id} succeded")


@package_cmd.command()
@click.pass_context
@click.option("--id")
def buildstatus(ctx, id):
    """
    View status for all builds, or build with specific id
    """
    if id:
        results = [get(f"builds/{id}")]
        _format_results(results, title=f"Build: {id}")
    else:
        results = get("builds").get("results")
        _format_results(results, title="Build Status")


def _format_results(results, title=""):
    """
    Helper function to organize table results using Rich

    Args:
        results: Results to format
        title: Optional table title

    Returns:
        None
    """
    table = Table(title=title, width=170)
    console = Console()
    count = 1
    for item in results:
        list = []
        for key in item:
            if count == 1:
                table.add_column(key.capitalize())
            list.append(str(item[key]))
        table.add_row(*list)
        count += 1
    console.print(table)
