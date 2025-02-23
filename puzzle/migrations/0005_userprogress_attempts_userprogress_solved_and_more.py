# Generated by Django 5.1.5 on 2025-02-14 20:14

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puzzle", "0004_remove_userprogress_attempts_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="userprogress",
            name="attempts",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprogress",
            name="solved",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprogress",
            name="solved_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name="userprogress",
            unique_together={("user", "puzzle")},
        ),
    ]
