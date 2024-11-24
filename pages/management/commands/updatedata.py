from django.core.management.base import BaseCommand
from django.db import IntegrityError
from teams.models import Player, WeeklyStat, Team

class Command(BaseCommand):
    help = 'Update lastSeasonPts field for each player with detailed output'

    def handle(self, *args, **kwargs):
        weeks = range(1, 15)
        top_scorer_positions = ['QB', 'HB', 'WR', 'TE']
        season_totals = {pos: {} for pos in top_scorer_positions}

        for week in weeks:
            weekly_stats = WeeklyStat.objects.filter(week=week).select_related('player').order_by('player__position', '-fantasy_points')
            
            for stat in weekly_stats:
                position = stat.player.position
                if position in season_totals:
                    if stat.player.id not in season_totals[position]:
                        season_totals[position][stat.player.id] = {
                            'player': stat.player,
                            'total_points': 0
                        }
                    season_totals[position][stat.player.id]['total_points'] += stat.fantasy_points

        for pos, players in season_totals.items():
            for player_data in players.values():
                player = player_data['player']
                total_points = player_data['total_points']

                try:
                    

                    # Update the player age
                    player.age += 1
                    
                    # Update the player total points from last season
                    player.lastSeasonPts = total_points

                    # Save the updates to the player
                    player.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated points for {player.name}'))
                except Player.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Player with ID {player.id} not found'))
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f'Integrity error while updating player {player.name}: {e}'))

        self.stdout.write(self.style.SUCCESS('Successfully updated lastSeasonPts for all players.'))
