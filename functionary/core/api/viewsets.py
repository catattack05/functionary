from typing import Optional

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from core.api import HEADER_PARAMETERS
from core.api.mixins import EnvironmentViewMixin


class EnvironmentGenericViewSet(EnvironmentViewMixin, GenericViewSet):
    """This viewset is intended for use in place of GenericViewSets where access
    control and queryset filtering should be done based on the appropriate environment
    for the request. The X-Environment-Id is used to determine the environment.

    For model based ViewSets with a queryset, the queryset must be filterable by an
    environment, either directly or through another field on the model. If the
    environment is defined through another field, declare that in the ViewSet class
    using:

        environment_through_field = "somefield"
    """

    environment_through_field: Optional[str] = None

    def get_queryset(self):
        """Filters the ViewSet queryset down to the appropriate objects based on the
        request environment context."""

        if self.environment_through_field:
            environment_field = f"{self.environment_through_field}__environment"
        else:
            environment_field = "environment"

        return (
            super().get_queryset().filter(**{environment_field: self.get_environment()})
        )


@extend_schema_view(
    create=extend_schema(parameters=HEADER_PARAMETERS),
    retrieve=extend_schema(parameters=HEADER_PARAMETERS),
    list=extend_schema(parameters=HEADER_PARAMETERS),
    update=extend_schema(parameters=HEADER_PARAMETERS),
    destroy=extend_schema(parameters=HEADER_PARAMETERS),
)
class EnvironmentModelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    EnvironmentGenericViewSet,
):
    """Replacement for ModelViewSet that provides queryset filtering and access
    control based on the requesting user's environment permissions.

    The ViewSet's queryset must be filterable by an environment, either directly or
    through another field on the model. If the environment is defined through another
    field, declare that in the ViewSet class using:

        environment_through_field = "somefield"
    """

    pass


@extend_schema_view(
    list=extend_schema(parameters=HEADER_PARAMETERS),
    retrieve=extend_schema(parameters=HEADER_PARAMETERS),
)
class EnvironmentReadOnlyModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    EnvironmentGenericViewSet,
):
    """Replacement for ReadOnlyModelViewSet that provides queryset filtering and access
    control based on the requesting user's environment permissions.

    The ViewSet's queryset must be filterable by an environment, either directly or
    through another field on the model. If the environment is defined through another
    field, declare that in the ViewSet class using:

        environment_through_field = "somefield"
    """

    pass
