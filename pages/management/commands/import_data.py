from django.core.management.base import BaseCommand
from django.db import IntegrityError
from teams.models import Player, WeeklyStat, Team
import pandas as pd


# Command to put the data from the CSV file into the database
class Command(BaseCommand):
    help = 'Import data from CSV files into the database'

    def handle(self, *args, **options):


        df_rec = pd.read_csv('content\CACT7_receiving.csv')
        df_pass = pd.read_csv('content\CACT7_passing.csv')
        df_rush = pd.read_csv('content\CACT7_rushing.csv')

        # Setting the dataframes to just the player name and their fantasy points
        df_rec = df_rec[['player__position', 'team__abbrName', 'player__rosterId', 'player__fullName', 'recTotalCatches', 'recTotalYds', 'recTotalTDs']]
        df_rec = df_rec.rename(columns={"player__fullName" : "fullName"})

        df_pass = df_pass[['player__position', 'team__abbrName', 'player__rosterId', 'player__fullName', 'passTotalYds', 'passTotalTDs', 'passTotalInts']]
        df_pass = df_pass.rename(columns={"player__fullName" : "fullName"})

        df_rush = df_rush[['player__position', 'team__abbrName', 'player__rosterId', 'player__fullName', 'rushTotalYds', 'rushTotalTDs', 'rushTotalFum']]
        df_rush = df_rush.rename(columns={"player__fullName" : "fullName"})
        
        # Start by merging the passing dataframe with the rushing dataframe
        df_combined = pd.merge(df_pass, df_rush, on=['player__position', 'team__abbrName', 'player__rosterId', 'fullName'], how='outer')

        # Now merge the combined dataframe with the receiving dataframe
        df_combined = pd.merge(df_combined, df_rec, on=['player__position', 'team__abbrName', 'player__rosterId', 'fullName'], how='outer')
        df_combined.fillna(0, inplace=True)

        df_combined['fantasyPoints'] = df_combined['recTotalYds'] / 10 + df_combined['recTotalTDs'] * 6 + df_combined['passTotalYds'] / 25 + df_combined['passTotalTDs'] * 4 - df_combined['passTotalInts'] * 2 + df_combined['rushTotalYds'] / 10 + df_combined['rushTotalTDs'] * 6 - df_combined['rushTotalFum'] * 2
         # Iterate over the DataFrame rows
        for index, row in df_combined.iterrows():
            try:
                player = Player.objects.get(rosterId=row['player__rosterId'])
                player.lastSeasonPts = row['fantasyPoints']
                player.save()
                self.stdout.write(self.style.SUCCESS(f'Updated points for {player.name}'))
            except Player.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Player with rosterId {row["player__rosterId"]} not found'))
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'Integrity error while updating player: {e}'))
        self.stdout.write(self.style.SUCCESS('Successfully imported player data'))

        


