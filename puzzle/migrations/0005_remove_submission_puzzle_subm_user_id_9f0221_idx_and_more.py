# Generated by Django 5.1.5 on 2025-02-21 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puzzle", "0004_submission_status_alter_puzzle_points_and_more"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="submission",
            name="puzzle_subm_user_id_9f0221_idx",
        ),
        migrations.RemoveField(
            model_name="submission",
            name="status",
        ),
        migrations.AlterField(
            model_name="puzzle",
            name="points",
            field=models.IntegerField(default=10),
        ),
    ]
