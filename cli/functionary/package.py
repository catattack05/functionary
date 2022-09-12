import os
import pathlib
import shutil
import tarfile

import click
from rich.text import Text
from rich.console import Console

from .client import get, post
from .config import get_config_value
from .utils import format_results


def create_languages() -> list[str]:
    spec = pathlib.Path(__file__).parent.resolve() / "templates"
    return [str(loc.name) for loc in spec.glob("*")]


def generateYaml(output_dir: str, name: str, language: str):
    package_path = pathlib.Path(output_dir).resolve() / name / "package.yaml"
    template_path = (
        pathlib.Path(__file__).parent.resolve() / "templates" / "template.yaml"
    )

    with template_path.open(mode="r") as temp, package_path.open(mode="a") as new:
        filedata = temp.read()
        filedata = filedata.replace("__PACKAGE_LANGUAGE__", language)
        filedata = filedata.replace("__PACKAGE_NAME__", name)
        new.write(filedata)


@click.group("package")
@click.pass_context
def package_cmd(ctx):
    pass


@package_cmd.command("create")
@click.option(
    "--language",
    "-l",
    type=click.Choice(create_languages(), case_sensitive=False),
    required=True,
)
@click.option("--output-directory", "-o", type=click.Path(exists=True), default=".")
@click.argument("name", type=str)
@click.pass_context
def create_cmd(ctx, language, name, output_directory):
    """
    Generate a function.

    Create an example function in the specified language.
    """
    dir = pathlib.Path(output_directory) / name
    if not dir.exists():
        dir.mkdir()

    basepath = pathlib.Path(__file__).parent.resolve() / "templates" / language

    shutil.copytree(str(basepath), str(dir), dirs_exist_ok=True)
    generateYaml(output_directory, name, language)

    click.echo()
    click.echo(f"Package creation for {name} successful!\n")
    text = Text()
    console = Console()
    text.append("Next Steps: \n", style="b u blue")
    text.append("* ", style="b blue")
    text.append("Write your functions in the generated functions.py \n")
    text.append("* ", style="b blue")
    text.append("Update the package.yaml with your package and function information \n")
    text.append("* ", style="b blue")
    text.append("When ready, publish the package to your environment by running: \n")
    text.append(
        f"    functionary package publish {output_directory}/{name}\n", style="b"
    )
    console.print(text)


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
    host = get_config_value("host", raise_exception=True)

    full_path = pathlib.Path(path).resolve()
    tarfile_name = full_path.joinpath(f"{full_path.name}.tar.gz")
    with tarfile.open(str(tarfile_name), "w:gz") as tar:
        tar.add(str(full_path), arcname="")

    with open(tarfile_name, "rb") as upload_file:
        click.echo(f"Publishing {str(tarfile_name)} package to {host}")
        response = post("publish", files={"package_contents": upload_file})
        id = response["id"]
        click.echo(f"Package upload complete\nBuild id: {id}")


@package_cmd.command()
@click.pass_context
@click.option("--id", help="check the status of a specific build with given id")
def buildstatus(ctx, id):
    """
    View status for all builds, or build with specific id
    """
    if id:
        results = get(f"builds/{id}")
        format_results([results], title=f"Build: {id}", excluded_fields=["environment"])
    else:
        results = get("builds")
        format_results(results, title="Build Status", excluded_fields=["environment"])


@package_cmd.command()
@click.pass_context
def list(ctx):
    """
    View all current packages and their functions
    """
    packages = get("packages")
    functions = get("functions")
    functions_lookup = {}

    for function in functions:
        package_id = function["package"]
        function_dict = {}
        function_dict["Function"] = function["name"]
        function_dict["Display Name"] = function["display_name"]
        function_dict["Description"] = function["description"]

        if package_id in functions_lookup:
            functions_lookup[package_id].append(function_dict)
        else:
            functions_lookup[package_id] = [function_dict]

    for package in packages:
        name = package["name"]
        id = package["id"]
        description = package["description"]
        associated_functions = functions_lookup[id]
        title = Text(f"{name}", style="bold blue")
        title.append(f"\n{description}", style="blue dim")
        format_results(associated_functions, title=title)
        click.echo("\n")
