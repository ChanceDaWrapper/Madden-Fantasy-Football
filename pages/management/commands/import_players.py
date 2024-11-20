# teams/management/commands/import_players.py
from django.core.management.base import BaseCommand
from teams.models import Player
import pandas as pd

# Class to import all the players of the league that current season
class Command(BaseCommand):
    help = 'Import player data from a CSV file'

    def handle(self, *args, **options):
        
        # Load the player data from a CSV file
        df_players = pd.read_csv('content\MC_players.csv')
        valid_positions = ['QB', 'HB', 'WR', 'TE']
        df_players = df_players[df_players['position'].isin(valid_positions)]

        # Process each row in the DataFrame
        for _, row in df_players.iterrows():
            player, created = Player.objects.get_or_create(
                rosterId=row['rosterId'],
                defaults={  # Values for new players
                    'name': row['fullName'],
                    'team': row['team'],
                    'age': row['age'],
                    'height': row['height'],
                    'weight': row['weight'],
                    'portraitId': row['portraitId'],
                    'position': row['position'],
                    'lastSeasonPts': 0,
                    'drafted': False
                }
            )
            
            if not created:
                # Update all fields except lastSeasonPts
                player.name = row['fullName']
                player.team = row['team']
                player.age = row['age']
                player.height = row['height']
                player.weight = row['weight']
                player.portraitId = row['portraitId']
                player.position = row['position']
                player.drafted = False  # or True, based on your logic
                player.save()

        self.stdout.write(self.style.SUCCESS('Successfully imported player data'))

        