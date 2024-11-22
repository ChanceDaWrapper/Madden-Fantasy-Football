# Generated by Django 5.0.4 on 2024-11-19 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0008_team_draftpick'),
    ]

    operations = [
        migrations.CreateModel(
            name='DraftState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_team_index', models.IntegerField(default=0)),
                ('draft_direction', models.IntegerField(default=1)),
                ('pick_counter', models.IntegerField(default=1)),
                ('round_counter', models.IntegerField(default=1)),
                ('is_round_reversed', models.BooleanField(default=False)),
            ],
        ),
    ]