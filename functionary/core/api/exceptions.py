from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Exception handler to add code from custom exceptions
    to response.

    Args:
        -exc: the exception to handle
        -context: dictionary containing any extra
         context such as the view currently being handled
    Returns:
        -The exception response with the additional error code.
        Unhandled exceptions return None, resulting in a 500 error
    """
    response = exception_handler(exc, context)
    if response is not None:
        response.data["code"] = exc.get_codes()

    return response


class BadRequest(APIException):
    """Default error handling exceptions for invalid requests to the system"""

    status_code = 400
    default_detail = "Request is invalid"
    default_code = "bad_request"


class MissingEnvironmentHeader(APIException):
    """Required environment header is missing"""

    status_code = 400
    default_detail = "X-Environment-Id or X-Team-Id header must be set"
    default_code = "missing_env_header"


class InvalidEnvironmentHeader(APIException):
    """Required environment header is present but invalid"""

    status_code = 400
    default_detail = "X-Environment-Id or X-Team-Id header must be valid"
    default_code = "invalid_env_header"


class InvalidTeamIDHeader(APIException):
    """Provided TeamID header is invalid"""

    status_code = 400
    default_detail = "Invalid X-Team-Id header must be set"
    default_code = "invalid_teamid_header"
