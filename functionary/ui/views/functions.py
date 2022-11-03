from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.auth import Permission
from core.models import Environment, Function, Task

from ..forms.forms import TaskParameterForm
from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class FunctionListView(PermissionedEnvironmentListView):
    model = Function
    environment_through_field = "package"
    queryset = Function.objects.select_related("package").all()
    order_by_fields = ["package__name", "name"]


class FunctionDetailView(PermissionedEnvironmentDetailView):
    model = Function
    environment_through_field = "package"

    def get_queryset(self):
        return super().get_queryset().select_related("package", "package__environment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        function = self.get_object()
        env = function.package.environment
        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            form = TaskParameterForm(function)

            context["form"] = form.render("forms/task_parameters.html")
        return context


@require_POST
@login_required
def execute(request) -> HttpResponse:
    func = None
    form = None

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if request.user.has_perm(Permission.TASK_CREATE, env):
        func = Function.objects.get(id=request.POST["function_id"])
        form = TaskParameterForm(func, request.POST)

        if form.is_valid():
            # Create the new Task, the validated parameters are in form.cleaned_data
            task = Task.objects.create(
                environment=env,
                creator=request.user,
                function=func,
                parameters=form.cleaned_data,
                return_type=func.return_type,
            )

            # redirect to a new URL:
            return HttpResponseRedirect(reverse("ui:task-detail", args=(task.id,)))
        args = {"form": form, "function": func}
        return render(request, "core/function_detail.html", args)

    return HttpResponseForbidden()
