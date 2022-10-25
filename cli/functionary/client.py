import click
import requests

from .config import get_config_value


def get(endpoint):
    """
    Gets any data associated with an endpoint from the api

    Args:
        endpoint: the name of the endpoint to get data from

    Returns:
        Data from endpoint as Python list/dict

    """
    response = _send_request(endpoint, "get")
    response_data = response.json()

    if "results" in response_data:
        return response_data["results"]
    else:
        return response_data


def post(endpoint, data=None, files=None):
    """
    Post provides data or files to endpoint

    Args:
        endpoint: the name of the endpoint to get data from
        data: Any data to put in the request's data field
        files: Any files to put in the request's files field

    Returns:
        Response from endpoint as Python list/dict

    """
    response = _send_request(endpoint, "post", post_data=data, post_files=files)
    return response.json()


def _400_error_handling(response):
    """
    Helper function for _send_request that gives more user friendly
    responses from 400 error codes

    Args:
        response: Python response object with 400 error
    Raises:
        ClickException with user friendly message based on response
    """
    message = None
    code = response.json()["code"]

    match code:
        case "missing_env_header":
            message = (
                "No environment selected. Please set environment id "
                + "using 'functionary package environment set'."
            )
        case "invalid_env_header":
            message = (
                "Invalid environment provided. Please set environment "
                + "using 'functionary package environment set'."
            )
        case "invalid_package":
            message = f"{response.json()['detail']}"
    if message is None:
        message = f"{response.json()['detail']}"
    raise click.ClickException(message)


def _send_request(endpoint, request_type, post_data=None, post_files=None):
    """
    Helper function for get and post that sends the request and handles any errors
    that arise

    Args:
        endpoint: the name of the endpoint to get data from
        request_type: Either post or get
        post_data: Any data to put in the post request's data field
        post_files: Any files to put in the post request's files field

    Returns:
        Response object generated from the request

    Raises:
        ClickException: Raised if cannot connect to host, permission issue
        exists, user has not set a required field, or other request failure

    """
    host = get_config_value("host", raise_exception=True)
    url = host + f"/api/v1/{endpoint}"
    headers = {}
    try:
        if (token := get_config_value("token", raise_exception=False)) is not None:
            headers["Authorization"] = f"Token {token}"

        if (
            environment_id := get_config_value(
                "current_environment_id", raise_exception=False
            )
        ) is not None:
            headers["X-Environment-ID"] = f"{environment_id}"

        if request_type == "post":
            response = requests.post(
                url, headers=headers, data=post_data, files=post_files
            )
        else:
            response = requests.get(url, headers=headers)

    except requests.ConnectionError:
        raise click.ClickException(f"Could not connect to {host}")
    except requests.Timeout:
        raise click.ClickException(f"Timeout occurred waiting for {host}")

    if response.ok:
        return response
    elif response.status_code == 400:
        _400_error_handling(response)
    elif response.status_code == 401:
        raise click.ClickException("Authentication failed. Please login and try again.")
    elif response.status_code == 403:
        raise click.ClickException("You do not have access to perform this action.")
    else:
        raise click.ClickException(
            f"Request failed: {response.status_code}\n" f"\tResponse: {response.text}"
        )
