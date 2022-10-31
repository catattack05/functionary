from django.db import models


class BuildLog(models.Model):
    """Log output from the completion of a Build"""

    build = models.OneToOneField(primary_key=True, to="Build", on_delete=models.CASCADE)
    log = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
