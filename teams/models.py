from django.db import models
from django.utils import timezone
# Create your models here.
class Player(models.Model):
    name = models.CharField(max_length=200)
    rosterId = models.PositiveIntegerField()  # Assuming roster ID is always positive
    team = models.CharField(max_length=100)
    age = models.PositiveIntegerField()  # Age is typically a positive integer
    height = models.PositiveIntegerField()  # Height could be stored in cm as a positive integer
    weight = models.PositiveIntegerField()  # Weight could be stored in kg as a positive integer
    portraitId = models.PositiveIntegerField()  # Portrait ID is a positive integer
    position = models.CharField(max_length=10)  # Position usually is a short string like 'QB'
    lastSeasonPts = models.PositiveIntegerField()  # Points are typically positive
    drafted = models.BooleanField(default=False)  # Boolean should have a default value
    
    def __str__(self):
        return self.name  # A string representation of the model, typically using the player's name


class WeeklyStat(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='weekly_stats')
    week = models.PositiveIntegerField()
    passing_yards = models.PositiveIntegerField(default=0)
    rushing_yards = models.PositiveIntegerField(default=0)
    receiving_yards = models.PositiveIntegerField(default=0)
    passing_tds = models.PositiveIntegerField(default=0)
    rushing_tds = models.PositiveIntegerField(default=0)
    receiving_tds = models.PositiveIntegerField(default=0)
    receptions = models.PositiveIntegerField(default=0)
    fantasy_points = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    date_added = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('player', 'week')


class Position(models.Model):
    POSITION_CHOICES = [
        ('QB', 'Quarterback'),
        ('RB1', 'Running Back 1'),
        ('RB2', 'Running Back 2'),
        ('WR1', 'Wide Receiver 1'),
        ('WR2', 'Wide Receiver 2'),
        ('TE', 'Tight End'),
        ('RQB', 'Reserve Quarterback'),
        ('RRB', 'Reserve Running Back'),
        ('RWR', 'Reserve Wide Receiver'),
        ('RTE', 'Reserve Tight End')
    ]
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='positions')
    position = models.CharField(max_length=3, choices=POSITION_CHOICES)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='positions')


class Team(models.Model):
    name = models.CharField(max_length=20) # The teams name
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    totalPoints = models.PositiveIntegerField(default=0)

    def draft_player(self, player, position):
        # Logic to add player to the team in the given position
        Position.objects.create(player=player, position=position, team=self)

    def cut_player(self, player):
        # Logic to remove player from the team
        Position.objects.filter(player=player, team=self).delete()

    def get_roster(self):
        # Logic to get the team's roster in the desired order
        return self.positions.all().order_by('position')
    