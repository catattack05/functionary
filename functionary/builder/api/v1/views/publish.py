from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ParseError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from builder.exceptions import InvalidPackage
from builder.utils import extract_package_definition, initiate_build
from core.api import HEADER_PARAMETERS
from core.api.mixins import EnvironmentViewMixin
from core.api.permissions import HasEnvironmentPermissionForAction

from ..serializers import BuildSerializer, PackageDefinitionWithVersionSerializer


class PublishView(APIView, EnvironmentViewMixin):
    """View for submitting a package to be built and published."""

    parser_classes = [MultiPartParser]
    permission_classes = [HasEnvironmentPermissionForAction]
    permissioned_model = "Package"

    # TODO: Add reference to package description YAML documentation once it exists
    @extend_schema(
        description=("Publish a package"),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "package_contents": {
                        "type": "string",
                        "format": "binary",
                        "description": "gzipped tarball containing the package files",
                    },
                },
            }
        },
        responses={200: BuildSerializer},
        parameters=HEADER_PARAMETERS,
    )
    def post(self, request, *args, **kwargs):
        """Receives the package contents and package definition files. The definition
        file is validated and then a new Build is created
        """
        # BinaryField is not supported by drf serializers, so we must validate the
        # request data ourselves
        self._validate_publish_input(request)

        environment = self.get_environment()
        package_contents_blob = request.FILES.get("package_contents").read()

        # TO-DO: put invalid package yaml class here
        try:
            package_yaml = extract_package_definition(package_contents_blob)
        except InvalidPackage:
            raise InvalidPackage("Could not extract package.yaml from package tarball")

        # If the package definition schema changes at any point, this would need to
        # identify the correct serializer based on the package_definition_version
        serializer = PackageDefinitionWithVersionSerializer(data=package_yaml)
        # TO-DO: put invalid package yaml class here
        if not serializer.is_valid():
            raise InvalidPackage(
                f"Invalid package.yaml. Encountered error: {serializer.errors}"
            )
        package_definition = serializer.validated_data["package"]

        build = initiate_build(
            creator=request.user,
            environment=environment,
            package_contents=package_contents_blob,
            package_definition=package_definition,
            package_definition_version=package_yaml.get("version", "1.0"),
        )

        return Response(BuildSerializer(build).data)

    def _validate_publish_input(self, request):
        """Validates that the request includes all required data"""
        if request.FILES.get("package_contents") is None:
            raise ParseError(detail="package_contents is required and must be a file")
