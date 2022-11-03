""" Function model """
import uuid

from django.core.exceptions import ValidationError
from django.db import models


def list_of_strings(value):
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return

    raise ValidationError(
        '"%(value)s" is not a list of strings', params={"value": value}
    )


class Function(models.Model):
    """Function is a unit of work that can be tasked

    Attributes:
        id: unique identifier (UUID)
        package: the package that the function is a part of
        name: internal name that published package definition keys off of
        display_name: optional display name
        summary: short description of the function
        description: more details about the function
        variables: list of variable names to set before execution
        return_type: the type of the object being returned
        schema: the function's OpenAPI definition
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(
        to="Package", on_delete=models.CASCADE, related_name="functions"
    )

    # TODO: This shouldn't be changeable after creation
    name = models.CharField(max_length=64, blank=False)

    display_name = models.CharField(max_length=64, null=True)
    summary = models.CharField(max_length=128, null=True)
    description = models.TextField(null=True)
    variables = models.JSONField(
        default=list, validators=[list_of_strings], blank=True, null=True
    )
    return_type = models.CharField(max_length=64, null=True)
    schema = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["package", "name"], name="package_name_unique_together"
            )
        ]

    def __str__(self):
        return self.name
