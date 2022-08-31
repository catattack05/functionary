import pathlib
import shutil
import tarfile

import click
import yaml

from .client import get, post
from .config import get_config_value
from .utils import format_results


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
@click.option("--id", help="view a specific package with the given id")
def view(ctx, id):
    """
    View all current packages and their functions
    """
    packages = get("packages")
    functions = get("functions")
    if id:
        name = ""
        description = ""
        found = False
        for package in packages:
            if package["id"] == id:
                name = package["name"]
                description = package["description"]
                found = True
        if found:
            associated_functions = []
            for function in functions:
                if function["package"] == id:
                    function_dict = {}
                    function_dict["Function Name"] = function["name"]
                    function_dict["Display Name"] = function["display_name"]
                    function_dict["Description"] = function["description"]
                    associated_functions.append(function_dict)
            format_results(
                associated_functions,
                title=f"{name}\n {description}",
            )
        else:
            click.echo(f"Package with id {id} not found")
    else:
        for i in range(0, len(packages)):
            package = packages[i]
            name = package["name"]
            description = package["description"]
            associated_functions = []
            for function in functions:
                if function["package"] == package["id"]:
                    function_dict = {}
                    function_dict["Function Name"] = function["name"]
                    function_dict["Display Name"] = function["display_name"]
                    function_dict["Description"] = function["description"]
                    associated_functions.append(function_dict)
            format_results(
                associated_functions,
                title=f"{name} \n {description}",
            )
            if i != len(packages) - 1:
                click.echo("\n")
