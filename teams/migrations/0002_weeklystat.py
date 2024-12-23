# Generated by Django 4.2.7 on 2024-01-25 07:42

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyStat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("week", models.PositiveIntegerField()),
                ("passing_yards", models.PositiveIntegerField(default=0)),
                ("rushing_yards", models.PositiveIntegerField(default=0)),
                ("receiving_yards", models.PositiveIntegerField(default=0)),
                ("passing_tds", models.PositiveIntegerField(default=0)),
                ("rushing_tds", models.PositiveIntegerField(default=0)),
                ("receiving_tds", models.PositiveIntegerField(default=0)),
                ("receptions", models.PositiveIntegerField(default=0)),
                (
                    "fantasy_points",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
                ),
                ("date_added", models.DateField(default=django.utils.timezone.now)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weekly_stats",
                        to="teams.player",
                    ),
                ),
            ],
            options={
                "unique_together": {("player", "week")},
            },
        ),
    ]
