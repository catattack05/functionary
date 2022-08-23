""" UserRole models """
from django.conf import settings
from django.db import models

from core.auth import Role

ROLE_CHOICES = [(role.name, role.value) for role in Role]


class UserRole(models.Model):
    """Base model for common components of TeamUserRole and EnvironmentUserRole"""

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(class)ss"
    )

    role = models.CharField(max_length=64, choices=ROLE_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TeamUserRole(UserRole):
    """Tracks what users are on which teams and their roles

    Attributes:
        user: Foreign key to User
        team: Foreign key to Team
        role: The user's role on the team
    """

    team = models.ForeignKey(
        to="Team", db_index=True, on_delete=models.CASCADE, related_name="user_roles"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "team"], name="unique_user_team")
        ]

    def __str__(self):
        return f"{self.team.name} - {self.user.username} - {self.role}"


class EnvironmentUserRole(UserRole):
    """Tracks what users are on which environments and their roles

    Attributes:
        user: Foreign key to User
        environment: Foreign key to Environment
        role: The user's role on the environment
    """

    environment = models.ForeignKey(
        to="Environment",
        db_index=True,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "environment"],
                name="unique_user_environment",
            )
        ]

    def __str__(self):
        return f"{self.environment.name} - {self.user.username} - {self.role}"
