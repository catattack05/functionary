from builder.models import Build, BuildLog

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class BuildListView(PermissionedEnvironmentListView):
    model = Build
    order_by_fields = ["id"]


class BuildDetailView(PermissionedEnvironmentDetailView):
    model = Build

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["build_log"] = BuildLog.objects.filter(build=context["object"])[0]
        return context
