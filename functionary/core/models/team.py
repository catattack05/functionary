""" Team model """
import uuid

from django.apps import apps
from django.db import models

from core.models import ModelSaveHookMixin


class Team(ModelSaveHookMixin, models.Model):
    """Namespace that teams of users work under

    Attributes:
        id: unique identifier (UUID)
        name: the name of the team
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True, db_index=True)

    def __str__(self):
        return self.name

    def post_create(self):
        """Post create hooks"""
        Environment = apps.get_model("core", "Environment")
        Environment.objects.create(name="default", team=self)
