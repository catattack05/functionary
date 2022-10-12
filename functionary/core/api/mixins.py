from functools import cache
from typing import Union

from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from core.auth import Permission
from core.models import Environment, Team

from .exceptions import (
    InvalidEnvironmentHeader,
    InvalidTeamIDHeader,
    MissingEnvironmentHeader,
)


class EnvironmentViewMixin:
    """Provides handling of the X-Environment-Id and X-Team-Id headers to determine
    the environment context of the request."""

    @cache
    def get_environment(self) -> Environment:
        """Retrieve the Environment object that corresponds to either the environment
        with id X-Environment-Id or the default environment for the team with id
        X-Team-Id.

        Returns:
            The appropriate Environment object based on the request headers

        Raises:
            InvalidHeader: The headers were missing or the environment could not be
                           determined based on the header values
        """
        environment_id = self.request.headers.get("X-Environment-Id")
        team_id = self.request.headers.get("X-Team-Id")

        if environment_id:
            try:
                environment_obj = Environment.objects.get(id=environment_id)
            except (Environment.DoesNotExist, ValidationError):
                raise InvalidEnvironmentHeader(
                    f"No environment found with id {environment_id}"
                )
        elif team_id:
            try:
                team_obj = Team.objects.get(id=team_id)
            except (Team.DoesNotExist, ValidationError):
                raise InvalidTeamIDHeader(f"No team found with id {team_id}")

            try:
                environment_obj = team_obj.environments.get(default=True)
            except Environment.DoesNotExist:
                raise MissingEnvironmentHeader(
                    f"No default environment for team {team_id}. "
                    "X-Environment-Id header is required."
                )
        else:
            raise MissingEnvironmentHeader(
                "X-Environment-Id or X-Team-Id header must be set"
            )

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
