import pytest
from django.urls import reverse

from core.models import Function, Package, Task, Team


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
