import datetime
import io
import json
import logging
import os
import shutil
import tarfile
from typing import TypeVar
from uuid import UUID

import docker
import yaml
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.template.loader import get_template
from docker.errors import APIError, BuildError
from pydantic import Field, Json, create_model

from core.models import Environment, Function, Package, User

from .celery import app
from .exceptions import InvalidPackage
from .models import Build, BuildLog, BuildResource

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

    try:
        tarball = tarfile.open(fileobj=package_contents_io, mode="r")
    except tarfile.ReadError:
        raise InvalidPackage(
            "Could not untar package file. Make sure it is a valid gzipped tarball."
        )

    def close_files():
        package_contents_io.close()
        tarball.close()

    try:
        package_definition_io = tarball.extractfile("package.yaml")
    except KeyError:
        close_files()
        raise InvalidPackage("package.yaml not found")

    if package_definition_io is None:
        close_files()
        raise InvalidPackage("package.yaml found, but is not a regular file")

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
        package_obj = None

        try:
            package_obj = Package.objects.get(
                environment=environment, name=package_definition.get("name")
            )
        except Package.DoesNotExist:
            pass

        build = Build.objects.create(
            creator=creator, environment=environment, package=package_obj
        )

        BuildResource(
            build=build,
            package_contents=package_contents,
            package_definition=package_definition,
            package_definition_version=package_definition_version,
        ).save()

    build_package.delay(build_id=build.id)

    return build


def _format_log_string(build_results, push_results):
    """
    Helper function to transform results of docker
    push and docker build into more user friendly string.

    Args:
        build_results: itertools._tee object returned from docker build
        push_results: generator object returned from docker push

    Returns:
        string with both build and push information in more readable format
    """
    build_str = ""
    for line in build_results:
        line_str = ""
        for value in line.values():
            line_str = line_str + str(value) + " "
        build_str = build_str + line_str + "\n"

    push_str = ""
    for line in push_results:
        dict_line = json.loads(line.decode("utf-8"))
        if "status" in dict_line:
            status = dict_line["status"]
            if "id" in dict_line:
                id = dict_line["id"]
                line_str = f"{id}: {status}"
            else:
                line_str = status
        push_str = push_str + " " + line_str + "\n"

    return "BUILD RESULTS:\n" + build_str + "\nPUSH RESULTS:\n" + push_str


@app.task
def build_package(build_id: UUID):
    """Retrieve the resources for Build and use them to build and push the package
    docker image

    Args:
        build_id: ID of the build being executed
    """
    docker_client = docker.from_env()

    # TODO: Catch exceptions and record failures. Also, what happens to the image we
    #       pushed? Should it be deleted?
    logger.info(f"Starting build {build_id}")

    workdir = f"{settings.BUILDER_WORKDIR_BASE}/{build_id}"
    os.makedirs(workdir)

    build = Build.objects.select_related("environment").get(id=build_id)
    build.status = Build.IN_PROGRESS
    build.save()

    environment = build.environment
    package = build.package
    package_contents = build.resources.package_contents
    package_definition = build.resources.package_definition

    image_name, dockerfile = build.resources.image_details
    full_image_name = f"{settings.REGISTRY}/{image_name}"

    if not package:
        with transaction.atomic():
            package = _create_package_from_definition(
                package_definition, environment, image_name
            )
            build.package = package
            build.save()

    try:
        # Need to validate the potentially new function schema, but
        # don't save it until the build has finished.
        db_functions = _create_functions_from_definition(
            package_definition.get("functions"), package
        )
        _extract_package_contents(package_contents, workdir)
        _load_dockerfile_template(dockerfile, workdir)

        image, build_result = docker_client.images.build(
            path=workdir, pull=True, forcerm=True, tag=full_image_name
        )
        push_result = docker_client.images.push(full_image_name, stream=True)
        build.status = Build.COMPLETE
    except BuildError as exc:
        error_info = [str(line) for line in exc.build_log]
        build_log_message = "".join(error_info)
        build.status = Build.ERROR
    except APIError as exc:
        build_log_message = str(exc)
        build.status = Build.ERROR

    with transaction.atomic():
        # Build has succeeded, save all the things now
        if build.status == Build.COMPLETE:
            for func in db_functions:
                func.save()
            package.image_name = image_name
            package.save()

            build_log_message = _format_log_string(build_result, push_result)

        log = BuildLog.objects.create(build=build, log=build_log_message)
        build.save()
        log.save()

    logger.debug(f"Cleaning up remnants of build {build_id}")
    docker_client.images.remove(image.id)
    shutil.rmtree(workdir)

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
    template = get_template(dockerfile_template)
    context = {"registry": settings.REGISTRY}

    with open(f"{workdir}/Dockerfile", "w") as dockerfile:
        dockerfile.write(template.render(context=context))


def _create_package_from_definition(
    package_definition: dict, environment: Environment, image_name: str
) -> Package:
    """Create a package and functions from definition file"""
    # TODO: Manually parsing for now, but this should be codified somewhere, with
    #       the parsing informed by package_definition_version.
    name = package_definition.get("name")

    try:
        package_obj = Package.objects.get(environment=environment, name=name)
    except Package.DoesNotExist:
        package_obj = Package(
            environment=environment,
            name=name,
        )

    package_obj.display_name = package_definition.get("display_name")
    package_obj.summary = package_definition.get("summary")
    package_obj.description = package_definition.get("description")
    package_obj.language = package_definition.get("language")
    package_obj.save()

    return package_obj


def _create_functions_from_definition(definitions, package: Package):
    """Creates the functions in the package from the definition file"""
    db_functions = []
    for function_def in definitions:
        name = function_def.get("name")
        try:
            function_obj = Function.objects.get(package=package, name=name)
        except Function.DoesNotExist:
            function_obj = Function(package=package, name=name)

        function_obj.display_name = function_def.get("display_name")
        function_obj.summary = function_def.get("summary")
        function_obj.return_type = function_def.get("return_type")
        function_obj.output_format = function_def.get("output_format")
        function_obj.description = function_def.get("description")
        function_obj.schema = _generate_function_schema(
            name, function_def.get("parameters")
        )
        db_functions.append(function_obj)

    return db_functions


def _generate_function_schema(name: str, parameters) -> str:
    """Creates a pydantic model from the parameter definitions and returns the schema
    as a JSON string"""
    type_map = {
        "integer": int,
        "string": str,
        "text": TypeVar("text", str, bytes),
        "float": float,
        "boolean": bool,
        "date": datetime.date,
        "datetime": datetime.datetime,
        "json": TypeVar("json", Json, str),
    }
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
