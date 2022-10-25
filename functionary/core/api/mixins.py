from functools import cache
from typing import Union

from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from core.auth import Permission
from core.models import Environment

from .exceptions import InvalidEnvironmentHeader, MissingEnvironmentHeader


class EnvironmentViewMixin:
    """Provides handling of the X-Environment-Id header to determine
    the environment context of the request."""

    @cache
    def get_environment(self) -> Environment:
        """Retrieve the Environment object that corresponds to the environment
        with id X-Environment-Id

        Returns:
            The appropriate Environment object based on the request headers

        Raises:
            InvalidHeader: The headers were missing or the environment could not be
                           determined based on the header values
        """
        environment_id = self.request.headers.get("X-Environment-Id")

        if environment_id:
            try:
                environment_obj = Environment.objects.get(id=environment_id)
            except (Environment.DoesNotExist, ValidationError):
                raise InvalidEnvironmentHeader(
                    f"No environment found with id {environment_id}"
                )
        else:
            raise MissingEnvironmentHeader("X-Environment-Id header must be set")

        return environment_obj

    def verify_user_permission(self, permission: Union[Permission, str]) -> None:
        """Checks that request.user has the supplied permission for the environment
        that the request pertains to.

        Args:
            permission: The permission required to pass this check. Can be a Permission
                        enum or a str.

        Returns:
            None: The user has the supplied permission

        Raises:
            PermissionDenied: The user does not have the supplied permission
        """
        if not self.request.user.has_perm(permission, self.get_environment()):
            raise PermissionDenied
