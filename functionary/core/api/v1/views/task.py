from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from core.api import HEADER_PARAMETERS
from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.v1.serializers import (
    TaskCreateByIdSerializer,
    TaskCreateByNameSerializer,
    TaskCreateResponseSerializer,
    TaskLogSerializer,
    TaskResultSerializer,
    TaskSerializer,
)
from core.api.viewsets import EnvironmentGenericViewSet
from core.models import Task, TaskResult


@extend_schema_view(
    retrieve=extend_schema(parameters=HEADER_PARAMETERS),
    list=extend_schema(parameters=HEADER_PARAMETERS),
)
class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    EnvironmentGenericViewSet,
):
    """View for creating and retrieving tasks"""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [HasEnvironmentPermissionForAction]

    def get_serializer_class(self):
        if self.action == "create":
            if "function_name" in self.request.data.keys():
                return TaskCreateByNameSerializer
            else:
                return TaskCreateByIdSerializer
        else:
            return self.serializer_class

    @extend_schema(
        description=(
            "Execute a function. The function to be executed can be defined either "
            "by supplying function as a string uuid, or function_name and "
            "package_name."
        ),
        request=PolymorphicProxySerializer(
            component_name="TaskCreate",
            serializers={
                "create_by_id": TaskCreateByIdSerializer,
                "create_by_name": TaskCreateByNameSerializer,
            },
            resource_type_field_name=None,
        ),
        responses={
            status.HTTP_201_CREATED: TaskCreateResponseSerializer,
        },
        parameters=HEADER_PARAMETERS,
    )
    def create(self, request, *args, **kwargs):
        request_serializer = self.get_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        request_serializer.save(
            creator=self.request.user,
            environment=self.get_environment(),
        )

        response_serializer = TaskCreateResponseSerializer(request_serializer.instance)
        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        description="Retrieve the task results",
        parameters=HEADER_PARAMETERS,
        responses={status.HTTP_200_OK: TaskResultSerializer},
    )
    @action(methods=["get"], detail=True)
    def result(self, request, pk=None):
        task = self.get_object()

        if not TaskResult.objects.filter(task=task).exists():
            raise NotFound(f"No result found for task {pk}.")

        serializer = TaskResultSerializer(task)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Retrieve the task log output",
        parameters=HEADER_PARAMETERS,
        responses={status.HTTP_200_OK: TaskLogSerializer},
    )
    @action(methods=["get"], detail=True)
    def log(self, request, pk=None):
        task = self.get_object()

        try:
            serializer = TaskLogSerializer(task.tasklog)
        except ObjectDoesNotExist:
            raise NotFound(f"No log found for task {pk}.")

        return Response(serializer.data, status=status.HTTP_200_OK)
