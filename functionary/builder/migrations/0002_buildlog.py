# Generated by Django 4.1.1 on 2022-10-27 15:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("builder", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BuildLog",
            fields=[
                (
                    "build",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="builder.build",
                    ),
                ),
                ("log", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
