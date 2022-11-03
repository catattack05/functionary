""" Package model """
import uuid

from django.core.validators import RegexValidator
from django.db import models

VALID_VARIABLE_NAME = RegexValidator(
    regex="[A-Z_][A-Z0-9_]*",
    message="Invalid variable name. Characters must be in [A-Z0-9_]",
)


class Variable(models.Model):
    """A Variable is set in the runtime environment by the system
    prior to function execution. Variables set for an Environment
    will override ones set for the Team.

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this variable belongs to
        team: the team that this variable belongs to
        name: name of the variable to set
        description: more details about the package
        value: value of the variable
        protect: True to protect the value of this variable
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(
        "Environment",
        on_delete=models.CASCADE,
        related_name="vars",
        blank=True,
        null=True,
    )
    team = models.ForeignKey(
        "Team", on_delete=models.CASCADE, related_name="vars", blank=True, null=True
    )

    name = models.CharField(
        max_length=255, validators=[VALID_VARIABLE_NAME], blank=False
    )
    description = models.TextField(null=True)
    value = models.TextField(max_length=32767, blank=False)
    protect = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"],
                name="environment_variable_name_unique_together",
            ),
            models.UniqueConstraint(
                fields=["team", "name"],
                name="team_variable_name_unique_together",
            ),
            models.CheckConstraint(
                name="variable_only_one_team_or_environment",
                check=(
                    models.Q(team__isnull=True, environment__isnull=False)
                    | models.Q(team__isnull=False, environment__isnull=True)
                ),
            ),
        ]

    @property
    def parent(self):
        return self.team if self.team is not None else self.environment

    def __str__(self):
        return f"{self.name} - {self.parent.name}"
