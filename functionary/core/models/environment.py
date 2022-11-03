""" Environment model """
import uuid

from django.db import models


class Environment(models.Model):
    """Second tier of a namespacing under Team. Environments act as the primary point
    of association for packages, tasks, etc.

    Attributes:
        id: unique identifier (UUID)
        name: the name of the environment
        team: the Team that this environment belongs to
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    team = models.ForeignKey(
        to="Team", related_name="environments", on_delete=models.CASCADE, db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"], name="team_name_unique_together"
            ),
        ]

    def __str__(self):
        return f"{self.team.name} - {self.name}"

    def variables(self):
        """Retrieve the variables visible in this environment.

        This will return all variables associated with this
        Environment and add in any variables associated with the Team
        that haven't been overridden.
        """
        env_vars = self.vars.all()
        return env_vars | self.team.vars.exclude(name__in=env_vars.values("name"))
