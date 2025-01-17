from celery import Celery

app = Celery("builder")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = "builder"
