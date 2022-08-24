import json

import click
import requests

from .config import get_config_value


def get(endpoint):
    """
    Gets any data associated with an endpoint from the api

    Args:
        Endpoint: the name of the endpoint to get data from

    Returns:
        Data: Data from endpoint as Python list/dict

    """
    response = _send_request(endpoint, "get")
    data = json.loads(response.text).get("results")
    return data


def post(endpoint, data=None, files=None):
    """
    Post provides data or files to endpoint

    Args:
        Endpoint: the name of the endpoint to get data from
        Data: Any data to put in the request's data field
        Files: Any files to put in the request's files field

    Returns:
        Data: Response from endpoint as Python list/dict

    """
    response = _send_request(endpoint, "post", post_data=data, post_files=files)
    data = json.loads(response.text)
    return data


def _send_request(endpoint, request_type, post_data=None, post_files=None):
    """
    Helper function for get and post that sends the request and handles any errors
    that arise

    Args:
        Endpoint: the name of the endpoint to get data from
        Request_type: Either post or get
        Post_data: Any data to put in the post request's data field
        Post_files: Any files to put in the post request's files field

    Returns:
        Response: A Response object generated from the request

    Raises:
        ClickException: Raised if cannot connect to host, permission issue
        exists, user has not set a required field, or other request failure

    """
    host = get_config_value("host")
    url = host + f"/api/v1/{endpoint}"
    try:
        if endpoint == "api-token-auth" and request_type == "post":
            response = requests.post(url, data=post_data)
        else:
            token = get_config_value("token")
            if endpoint == "teams" and request_type == "get":
                headers = {"Authorization": f"Token {token}"}
                response = requests.get(url, headers=headers)
            else:
                try:
                    environment_id = get_config_value("current_environment_id")
                except click.ClickException:
                    raise click.ClickException(
                        "Please set an active environment id using 'environment set'"
                    )
                headers = {
                    "Authorization": f"Token {token}",
                    "X-Environment-ID": f"{environment_id}",
                }
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
    elif response.status_code == 401:
        raise click.ClickException("Authentication failed. Please login and try again.")
    elif response.status_code == 403:
        raise click.ClickException("You do not have access to perform this action.")
    else:
        raise click.ClickException(
            f"Request failed: {response.status_code}\n" f"\tResponse: {response.text}"
        )
