from rest_framework.exceptions import APIException


class InvalidPackage(APIException):
    """Exception for when the file provided for a build is not a valid package
    tarball"""

    status_code = 400
    default_detail = "Package is invalid"
    default_code = "invalid_package"
