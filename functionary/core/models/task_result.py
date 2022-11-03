import json

from django.db import models


class TaskResult(models.Model):
    """Results from the execution of a Task"""

    task = models.OneToOneField(primary_key=True, to="Task", on_delete=models.CASCADE)
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def json(self):
        """Return the result as loaded JSON rather than the raw string"""
        return json.loads(self.result)
