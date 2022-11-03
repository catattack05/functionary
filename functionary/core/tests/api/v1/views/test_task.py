import json

import pytest
from django.urls import reverse

from core.models import Function, Package, Task, TaskResult, Team


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    function_schema = {
        "title": "test",
        "type": "object",
        "properties": {"prop1": {"type": "integer"}},
    }
    return Function.objects.create(
        name="testfunction", package=package, schema=function_schema
    )


@pytest.fixture
def task(function, admin_user):
    return Task.objects.create(
        function=function,
        environment=function.package.environment,
        parameters={"prop1": "value1"},
        creator=admin_user,
    )


@pytest.fixture
def request_headers(environment):
    return {"HTTP_X_ENVIRONMENT_ID": str(environment.id)}


def test_create(admin_client, function, request_headers):
    """Create a Task"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"prop1": 5},
    }
    response = admin_client.post(
        url, data=task_input, content_type="application/json", **request_headers
    )
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_returns_400_for_invalid_parameters(
    admin_client, function, request_headers
):
    """Return a 400 for invalid tasking parameters"""
    url = reverse("task-list")

    task_input = {
        "function": str(function.id),
        "parameters": {"prop1": "not an integer"},
    }
    response = admin_client.post(
        url, data=task_input, content_type="application/json", **request_headers
    )

    assert response.status_code == 400
    assert not Task.objects.filter(function=function).exists()


def test_no_result_returns_404(admin_client, task, request_headers):
    """The task result is returned as the correct type"""

    url = f"{reverse('task-list')}{task.id}/result/"
    response = admin_client.get(url, **request_headers)

    assert response.status_code == 404


def test_result_type_is_preserved(admin_client, task, request_headers):
    """The task result is returned as the correct type"""
    url = f"{reverse('task-list')}{task.id}/result/"

    str_result = json.dumps("1234")
    int_result = json.dumps(1234)
    list_result = json.dumps([1, 2, 3, 4])
    dict_result = json.dumps({"one": 1, "two": 2, "three": 3, "four": 4})
    bool_result = json.dumps(True)

    task_result = TaskResult.objects.create(task=task)

    task_result.result = str_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is str

    task_result.result = int_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is int

    task_result.result = list_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is list

    task_result.result = dict_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is dict

    task_result.result = bool_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is bool
