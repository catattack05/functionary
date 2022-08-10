import io
import logging
import os
import shutil
import tarfile
from uuid import UUID

import docker
import yaml
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.template import Context, Engine
from pydantic import Field, create_model

from core.models import Environment, Function, Package, User

from .celery import app
from .models import Build, BuildResource

_docker_client = docker.from_env()

_dockerfile_home = f"{apps.get_app_config('builder').path}/resources/docker"

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


def extract_package_definition(package_contents: bytes) -> dict:
    """Extracts the package.yaml from a package tarball

    Args:
        package_contents: gzipped tarball of a package

    Returns:
        The package definition yaml loaded as a dict
    """
    package_contents_io = io.BytesIO(package_contents)
    tarball = tarfile.open(fileobj=package_contents_io, mode="r")

    def close_files():
        package_contents_io.close()
        tarball.close()

    try:
        package_definition_io = tarball.extractfile("package.yaml")
    except KeyError:
        # TODO: Raise custom, useful exception
        close_files()
        raise Exception("package.yaml not found")

    if package_definition_io is None:
        # TODO: Raise custom, useful exception
        close_files()
        raise Exception("package.yaml found, but is not a regular file")

    package_definition = yaml.safe_load(package_definition_io.read())
    close_files()

    return package_definition


def initiate_build(
    creator: User,
    environment: Environment,
    package_contents: bytes,
    package_definition: dict,
    package_definition_version: str,
) -> Build:
    """Creates the Build and BuildResource instances necessary to initiate a build and
    then creates the task for the worker that will perform the build.

    Args:
        creator: The User initiating the build
        environment: The environment that the package should be published under
        package_contents: A gzipped file containing the package to be built
        package_definition: dict containing the package definition
    """
    with transaction.atomic():
        build = Build(creator=creator)
        build.save()

        BuildResource(
            build=build,
            package_contents=package_contents,
            package_definition=package_definition,
            package_definition_version=package_definition_version,
        ).save()

    build_package.delay(build_id=build.id, environment_id=environment.id)

    return build


@app.task
def build_package(build_id: UUID, environment_id: UUID):
    """Retrieve the resources for Build and use them to build and push the package
    docker image

    Args:
        build_id: ID of the build being executed
        environment_id: The UUID of the Environment that the resultant package will be
                        assigned to
    """
    # TODO: Catch exceptions and record failures. Also, what happens to the image we
    #       pushed? Should it be deleted?
    logger.info(f"Starting build {build_id}")

    workdir = f"{settings.BUILDER_WORKDIR_BASE}/{build_id}"
    os.makedirs(workdir)
    build = Build.objects.get(id=build_id)
    package_contents = build.resources.package_contents
    package_definition = build.resources.package_definition

    # TODO: This sort of direct access of package_definition should be discouraged, as
    #       it results in package schema parsing being spread throughout the code. It
    #       should live in one place and we should call helpers in places like this.
    name = package_definition["name"]
    language = package_definition["language"]
    dockerfile = f"{language}.Dockerfile"
    image_name = f"{environment_id}/{name}:{build_id}"
    full_image_name = f"{settings.REGISTRY}/{image_name}"

    _extract_package_contents(package_contents, workdir)
    _load_dockerfile_template(dockerfile, workdir)

    image, build_log = _docker_client.images.build(
        path=workdir,
        pull=True,
        forcerm=True,
        tag=full_image_name,
    )

    _docker_client.images.push(full_image_name)

    logger.debug(f"Cleaning up remnants of build {build_id}")
    _docker_client.images.remove(image.id)
    shutil.rmtree(workdir)

    with transaction.atomic():
        package = _create_package_from_definition(
            package_definition, environment_id, image_name
        )
        build.status = Build.COMPLETE
        build.package = package
        build.save()

        # TODO: The Build model should just clean its own resources with post_save hook
        build.resources.delete()

    logger.info(f"Build {build_id} COMPLETE")


def _extract_package_contents(package_contents: bytes, workdir: str) -> None:
    """Extract the package tarball"""
    package_contents_io = io.BytesIO(package_contents)
    tarball = tarfile.open(fileobj=package_contents_io, mode="r")
    tarball.extractall(workdir)
    tarball.close()
    package_contents_io.close()


def _load_dockerfile_template(dockerfile_template: str, workdir: str) -> None:
    """Render the dockfile template and write it to the working directory"""
    template = Engine(dirs=[_dockerfile_home]).get_template(dockerfile_template)
    context = Context({"registry": settings.REGISTRY})

    with open(f"{workdir}/Dockerfile", "w") as dockerfile:
        dockerfile.write(template.render(context=context))


def _create_package_from_definition(
    package_definition: dict, environment_id: UUID, image_name: str
) -> Package:
    """Create a package and functions from definition file"""
    # TODO: Manually parsing for now, but this should be codified somewhere, with
    #       the parsing informed by package_definition_version.
    environment = Environment.objects.get(id=environment_id)
    name = package_definition.get("name")

    try:
        package_obj = Package.objects.get(environment=environment, name=name)
    except Package.DoesNotExist:
        package_obj = Package(
            environment=environment,
            name=name,
        )

    package_obj.display_name = package_definition.get("display_name")
    package_obj.description = package_definition.get("description")
    package_obj.language = package_definition.get("language")
    package_obj.image_name = image_name

    _create_functions_from_definition(package_definition.get("functions"), package_obj)
    package_obj.save()

    return package_obj


def _create_functions_from_definition(definitions, package: Package):
    """Creates the functions in the package from the definition file"""
    for function_def in definitions:
        name = function_def.get("name")
        try:
            function_obj = Function.objects.get(package=package, name=name)
        except Function.DoesNotExist:
            function_obj = Function(package=package, name=name)

        function_obj.display_name = function_def.get("display_name")
        function_obj.description = function_def.get("description")
        function_obj.schema = _generate_function_schema(
            name, function_def.get("parameters")
        )
        function_obj.save()


def _generate_function_schema(name: str, parameters) -> str:
    """Creates a pydantic model from the parameter definitions and returns the schema
    as a JSON string"""
    # TODO - Update this map to add lists and whatever other pieces we want to support
    type_map = {"int": int, "str": str}
    params_dict = {}

    for parameter in parameters:
        field = Field()
        field.alias = parameter.get("name")
        field.title = parameter.get("display_name", field.alias)
        field.description = parameter.get("description")
        field.default = parameter.get("default", ...)
        type_ = type_map[parameter["type"]]

        params_dict[field.alias] = (type_, field)

    model = create_model(name, **params_dict)

    return model.schema()
