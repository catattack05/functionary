import click
import requests
import json
from .config import get_config_value


def get(endpoint):
    """
    Gets any data associated with an endpoint from the api

    Args:
        Endpoint: the name of the endpoint to get data from

    Returns:
        Data: Data from endpoint as Python list/dict

    Raises:
        ClickException if failed connection, timeout, or could not retrieve endpoint

    """
    token = get_config_value("token")
    header = {"Authorization": f"Token {token}"}
    url = get_config_value("host") + f"/api/v1/{endpoint}"

    try:
        response = requests.get(url, headers=header)
    except requests.ConnectionError:
        raise click.ClickException("Could not connect to host")
    except requests.Timeout:
        raise click.ClickException("Timeout occured while trying to connect to host")

    if response.ok:
        data = json.loads(response.text).get("results")
        return data
    else:
        if response.status_code == 401:
            raise click.ClickException("Unauthorized request, try logging in again.")
        elif response.status_code == 403:
            raise click.ClickException("Request forbidden")
        else:
            raise click.ClickException(
                f"Failed to get {endpoint} endpoint: {response.status_code}\n"
                f"Response: {response.text}"
            )


def post(endpoint, data):
    """
    Post provided data to endpoint

    Args:
        Endpoint: the name of the endpoint to get data from

    Returns:
        Upload_Response: Response from endpoint as Python list/dict

    Raises:
        ClickException if failed connection, timeout, or could not retrieve endpoint
    """
    token = get_config_value("token")
    url = get_config_value("host") + f"/api/v1/{endpoint}"
    upload_response = None
    try:
        if endpoint == "publish":
            environment_id = json.loads(get_config_value("current_environment")).get(
                "id"
            )
            headers = {
                "Authorization": f"Token {token}",
                "X-Environment-ID": f"{environment_id}",
            }
            upload_response = requests.post(
                url, headers=headers, files={"package_contents": data}
            )
        if endpoint == "api-token-auth":
            upload_response = requests.post(url, data=data)
    except requests.ConnectionError:
        raise click.ClickException("Could not connect to host")
    except requests.Timeout:
        raise click.ClickException("Timeout occurred waiting for build")

    # check status code/message on return then exit
    if upload_response is not None:
        if upload_response.ok:
            return json.loads(upload_response.text)
        elif upload_response.status_code == 401:
            raise click.ClickException("Unauthorized request, try logging in again.")
        elif upload_response.status_code == 403:
            raise click.ClickException("Request forbidden")
        else:
            raise click.ClickException(
                f"Failed to build image: {upload_response.status_code}\n"
                f"\tResponse: {upload_response.text}"
            )
    else:
        raise click.ClickException("Could not make post request: invalid endpoint")
