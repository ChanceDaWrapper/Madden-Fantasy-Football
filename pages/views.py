# pages/views.py
from django.http import HttpResponse, JsonResponse, Http404
import json, random
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from teams.models import Team, Player, WeeklyStat, Position, Schedule, DraftState, PlayerSelection
from django.db.models import Prefetch
import pandas as pd
from operator import attrgetter

positions_global = None # Global positions variable for display in drafting.html

class HomePageView(TemplateView):
    print()
    template_name = 'home.html'
    
def playerData(request):

    draft_state, created = DraftState.objects.get_or_create(id=1)
    
    # Fetch teams ordered by their "DraftPick" field
    teams = Team.objects.order_by('draftPick')
    team_ids_ordered = [team.id for team in teams]

    # Debug print statement to ensure teams are listed correctly
    for team in teams:
        print(team.name)
    

    current_team_id = team_ids_ordered[draft_state.current_team_index]
    positions = Position.objects.filter(team_id=current_team_id)
    # Fetch all players from the database
    players = Player.objects.all().order_by('-lastSeasonPts')
    team = Team.objects.get(id=current_team_id)
    team_name = team.name
    
    # Fetch all selections from PlayerSelection
    selections = PlayerSelection.objects.all().order_by('round', 'pick')

    # Format the selections into the draft_list
    draft_list = [
        f"{selection.round}.{selection.pick}: {selection.team.name} -- {selection.player.position} {selection.player.name}"
        for selection in selections
    ]

    # Handle positions dynamically
    initial_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'RQB', 'RRB', 'RWR', 'RTE']
    positions_with_none = [{'position': pos, 'player': None} for pos in initial_positions]
    filled_positions = Position.objects.filter(team_id=current_team_id).select_related('player')
    filled_positions_dict = {pos.position: pos.player for pos in filled_positions}

    # Map players to their positions
    for position in positions_with_none:
        if position['position'] in filled_positions_dict:
            player = filled_positions_dict[position['position']]
            position['player'] = player.name if player else None


    return render(request, 'drafting.html', {'players': players, 'positions': positions_with_none, 'fantasy_team': team_name, 'draft_list': draft_list})



@require_http_methods(["GET", "POST"])
def teamCreate(request):
    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        if team_name:
            Team.objects.create(name=team_name)
            return redirect('team_create')
    
    teams = Team.objects.all()
    return render(request, 'team_create.html', {'teams': teams})


def addTeam(request):
    team_name = request.POST.get('team_create', '')
    if team_name:
        Team.objects.create(name = team_name)
    return redirect('team_create')

def deleteTeam(request, team_id):
    try:
        team = Team.objects.get(id=team_id)
        # Optionally handle related schedules here if not handled in model's delete method
        team.hometeam.all().delete()  # Deletes all related home games
        team.awayteam.all().delete()  # Deletes all related away games
        team.delete()
    except Team.DoesNotExist:
        raise Http404("Team not found.")
    return redirect('team_create')


@csrf_exempt
@require_http_methods(["POST"])
def draft_player(request):
    print("Draft Player endpoint hit")

    try:
        # Load or create the draft state
        draft_state, created = DraftState.objects.get_or_create(id=1)
        print(f"Draft state: {draft_state}")

        # Parse JSON data
        data = json.loads(request.body)
        player_id = data['playerId']
        position = data.get('universalSpot')
        print(f"Request data: {data}")


        # Fetch all teams and their IDs
        teams = Team.objects.order_by('draftPick')
        team_ids_ordered = [team.id for team in teams]
        print(f"Teams in order: {team_ids_ordered}")

        # Get the current team ID
        current_team_id = team_ids_ordered[draft_state.current_team_index]
        print(f"Current team ID: {current_team_id}")

        # Draft the player
        player = Player.objects.get(id=player_id)
        team = Team.objects.get(id=current_team_id)
        print(f"Drafting player {player.name} for team {team.name} at position {position}")

        team.draft_player(player, position)  # Assuming this method exists in your Team model
        player.drafted = True
        player.save()

        # Add to PlayerSelection
        PlayerSelection.objects.create(
            round=draft_state.round_counter,
            pick=draft_state.pick_counter,
            team=team,
            player=player,
        )

        draft_state.pick_counter += 1

        # Update draft state (team index and round management)
        draft_state.current_team_index += draft_state.draft_direction
        if draft_state.current_team_index >= len(team_ids_ordered) or draft_state.current_team_index < 0:
            draft_state.draft_direction *= -1  # Reverse direction for snake draft
            draft_state.current_team_index = max(0, min(draft_state.current_team_index, len(team_ids_ordered) - 1))
            draft_state.round_counter += 1
            draft_state.pick_counter = 1

        # Save updated draft state
        draft_state.save()

        # Handle positions logic
        initial_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'RQB', 'RRB', 'RWR', 'RTE']
        positions_with_none = [{'position': pos, 'player': None} for pos in initial_positions]
        filled_positions = Position.objects.filter(team_id=current_team_id).select_related('player')
        filled_positions_dict = {pos.position: pos.player for pos in filled_positions}

        # Map players to their positions
        for position in positions_with_none:
            if position['position'] in filled_positions_dict:
                player_swap = filled_positions_dict[position['position']]
                position['player'] = player_swap.name if player_swap else None

        # Update positions_global if needed (or return positions as needed)
        positions_global = positions_with_none

        return JsonResponse({'status': 'success', 'message': 'Player drafted successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data received.'}, status=400)
    except KeyError:
        return JsonResponse({'status': 'error', 'message': 'Missing playerId in data.'}, status=400)
    except Exception as e:
        print(f"Error: {str(e)}")  # Debugging
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



    
@csrf_exempt
def reset_players(request):
    # Reset global variables
    global positions_global
    positions_global = None

    try:

        draft_state, created = DraftState.objects.get_or_create(id=1)

        draft_state.current_team_index = 0
        draft_state.draft_direction = 1
        draft_state.pick_counter = 1
        draft_state.round_counter = 1
        draft_state.is_round_reversed = False

        draft_state.save()

        # Fetch all teams
        teams = list(Team.objects.all())

        # Randomize the order of teams for draft
        random.shuffle(teams)

        # Assign new draft order to teams based on random shuffle
        for index, team in enumerate(teams, start=1):
            team.draftPick = index
            team.save()

        # Print the new draft order
        for team in teams:
            print(f"Team: {team.name}, draftPick: {team.draftPick}")
        
        # Reset player and position data
        Position.objects.all().delete()  # Delete all position instances
        Player.objects.update(drafted=False)  # Reset drafted status for all players
        PlayerSelection.objects.all().delete()

        return redirect("team_create")
    except Exception as e:
        # Return an error response in case of failure
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
def rosters(request):
    # Requesting all teams from the Team model
    teams = Team.objects.all()

    # Create a dictionary to store the teams and rosters
    team_rosters = {}
    for team in teams:
        # Get the positions for each team
        # current_team_id = Team.object.filter(name = team)
        positions = Position.objects.filter(team=team)
        # Iterate through each position to access its fields
        for position in positions:
            print(position.player.name)  # Now correctly accessing the position field of each Position object
        
        initial_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'RQB', 'RRB', 'RWR', 'RTE']
        positions_with_none = [{'position': pos, 'player': None} for pos in initial_positions]
        # Assuming you have a queryset of filled positions from your database
        filled_positions = Position.objects.filter(team=team).select_related('player')

        # Convert filled_positions to a dictionary for efficient lookups
        filled_positions_dict = {pos.position: pos.player for pos in filled_positions}

        # Update positions_with_none with players from filled_positions where applicable
        for position in positions_with_none:
            if position['position'] in filled_positions_dict:
                playerSwap = filled_positions_dict[position['position']]
                position['player'] = playerSwap.name if playerSwap else None
        
        
        team_rosters[team] = positions_with_none

    return render(request, 'rosters.html', {'team_rosters': team_rosters})


from decimal import Decimal

# Calculate total fantasy points for primary positions
def calculate_fantasy_points(team, week, primary_positions, reserve_positions):
    total_points = 0.0
    used_positions = set()

    def get_best_player(position_group):
        players = [p for p in team if p.position in position_group]
        players_with_stats = [(p, WeeklyStat.objects.filter(player=p.player, week=week).first()) for p in players]
        players_with_stats = [(p, ws) for p, ws in players_with_stats if ws is not None]
        if not players_with_stats:
            return 0.0
        best_player_stat = max(players_with_stats, key=lambda item: float(item[1].fantasy_points))
        return float(best_player_stat[1].fantasy_points)

    # Best QB
    total_points += get_best_player(['QB'] + reserve_positions.get('QB', []))
    used_positions.add('QB')

    # Best 2 RBs
    rb_points = [get_best_player([pos]) for pos in ['RB1', 'RB2'] + reserve_positions.get('RB1', []) + reserve_positions.get('RB2', [])]
    rb_points.sort(reverse=True)
    total_points += sum(rb_points[:2])
    used_positions.update(['RB1', 'RB2'])

    # Best 2 WRs
    wr_points = [get_best_player([pos]) for pos in ['WR1', 'WR2'] + reserve_positions.get('WR1', []) + reserve_positions.get('WR2', [])]
    wr_points.sort(reverse=True)
    total_points += sum(wr_points[:2])
    used_positions.update(['WR1', 'WR2'])

    # Best TE
    total_points += get_best_player(['TE'] + reserve_positions.get('TE', []))
    used_positions.add('TE')

    return round(total_points, 2)

# Define primary positions and corresponding reserve positions
primary_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE']
reserve_positions = {
    'QB': ['RQB'],
    'RB1': ['RRB'],
    'RB2': ['RRB'],
    'WR1': ['RWR'],
    'WR2': ['RWR'],
    'TE': ['RTE']
}

def generate_playoff_matchups(week, teams):
    """Generate playoff matchups for a given week."""
    if len(teams) % 2 != 0:
        raise ValueError("Number of teams must be even for matchups")

    for i in range(len(teams) // 2):
        hometeam = teams[i]
        awayteam = teams[-(i + 1)]  # Pair teams by seed
        Schedule.objects.create(week=week, hometeam=hometeam, awayteam=awayteam)


@csrf_exempt
def matchups(request):
    weeks = range(1, 18)  # Assuming NFL weeks 1 through 17
    matchups_data = {}
    primary_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE']
    reserve_positions = {
        'QB': ['RQB'],
        'RB1': ['RRB'],
        'RB2': ['RRB'],
        'WR1': ['RWR'],
        'WR2': ['RWR'],
        'TE': ['RTE']
    }
    
    # Resetting the team objects ever reload. Slower and less effecient -- will change in the future
    Team.objects.update(wins=0, losses=0, totalPoints=0)


    for week in weeks:
        week_matchups = Schedule.objects.filter(week=week).select_related('hometeam', 'awayteam')
        for matchup in week_matchups:
            hometeam_roster = matchup.hometeam.get_roster_with_stats()
            awayteam_roster = matchup.awayteam.get_roster_with_stats()

            sorted_hometeam_roster = sorted(hometeam_roster, key=lambda p: primary_positions.index(p.position) if p.position in primary_positions else (len(primary_positions) + next((i for i, pos_list in enumerate(reserve_positions.values()) if p.position in pos_list), float('inf'))))
            sorted_awayteam_roster = sorted(awayteam_roster, key=lambda p: primary_positions.index(p.position) if p.position in primary_positions else (len(primary_positions) + next((i for i, pos_list in enumerate(reserve_positions.values()) if p.position in pos_list), float('inf'))))

            hometeam_points = calculate_fantasy_points(sorted_hometeam_roster, week, primary_positions, reserve_positions)
            awayteam_points = calculate_fantasy_points(sorted_awayteam_roster, week, primary_positions, reserve_positions)
            
            matchup.hometeam.roster = sorted_hometeam_roster
            matchup.awayteam.roster = sorted_awayteam_roster            
            matchup.hometeam.totalPoints = hometeam_points
            matchup.awayteam.totalPoints = awayteam_points

            # Determine the result and update wins/losses
            if hometeam_points > awayteam_points:
                matchup.hometeam.wins += 1
                matchup.awayteam.losses += 1
                matchup.hometeam.result_class = 'winner'
                matchup.awayteam.result_class = 'loser'
            elif hometeam_points < awayteam_points:
                matchup.awayteam.wins += 1
                matchup.hometeam.losses += 1
                matchup.hometeam.result_class = 'loser'
                matchup.awayteam.result_class = 'winner'
            else:
                matchup.hometeam.result_class = 'tie'
                matchup.awayteam.result_class = 'tie'

        matchups_data[week] = week_matchups

    # Gather top scorers for each position in each week
    top_scorers = {}
    top_scorer_positions = ['QB', 'HB', 'WR', 'TE']

    for week in weeks:
        weekly_stats = WeeklyStat.objects.filter(week=week).select_related('player').order_by('player__position', '-fantasy_points')
        week_top_scorers = {pos: [] for pos in top_scorer_positions}

        for stat in weekly_stats:
            position = stat.player.position
            if position in week_top_scorers and len(week_top_scorers[position]) < 5:
                week_top_scorers[position].append(stat)
        
        # Sort week_top_scorers by top_scorer_positions order
        sorted_week_top_scorers = {pos: week_top_scorers[pos] for pos in top_scorer_positions if pos in week_top_scorers}
        
        top_scorers[week] = sorted_week_top_scorers


    # Generate playoff rounds
    standings = Team.objects.order_by('-wins', '-totalPoints')  # Sort by wins, then total points
    if not Schedule.objects.filter(week=15).exists():  # Generate week 15 if it doesn't exist
        top_8 = standings[:8]  # Get top 8 teams
        generate_playoff_matchups(15, top_8)

    # Simulate playoff rounds dynamically
    current_week = 15
    while Schedule.objects.filter(week=current_week).exists():
        week_matchups = Schedule.objects.filter(week=current_week).select_related('hometeam', 'awayteam')
        winners = []

        for matchup in week_matchups:
            hometeam_roster = matchup.hometeam.get_roster_with_stats()
            awayteam_roster = matchup.awayteam.get_roster_with_stats()

            hometeam_points = calculate_fantasy_points(hometeam_roster, current_week, primary_positions, reserve_positions)
            awayteam_points = calculate_fantasy_points(awayteam_roster, current_week, primary_positions, reserve_positions)

            if hometeam_points > awayteam_points:
                winners.append(matchup.hometeam)  # Add winner to the list
            else:
                winners.append(matchup.awayteam)  # Add winner to the list

        if len(winners) > 1:  # If more than one team, create the next week's matchups
            generate_playoff_matchups(current_week + 1, winners)
        current_week += 1
        

    return render(request, 'matchups.html', {'matchups': matchups_data, 'weeks': weeks, 'top_scorers':top_scorers})








@csrf_exempt
def generate_schedule(request):
    Schedule.objects.all().delete()
    teams = list(Team.objects.order_by('id'))
    num_teams = len(teams)

    if num_teams % 2:
        teams.append(None)  # Adding a dummy team for bye-weeks

    # Ensure we are planning for 14 weeks
    total_weeks = 14

    # Generate the schedule for 14 weeks
    for week in range(total_weeks):
        for i in range(len(teams) // 2):
            home_team = teams[i]
            away_team = teams[-i - 1]
            if home_team is not None and away_team is not None:
                Schedule.objects.create(
                    week=week + 1, 
                    hometeam=home_team, 
                    awayteam=away_team
                )
        # Rotate the list of teams, keeping the first team fixed
        teams.insert(1, teams.pop())

    return redirect('Matchups')

@csrf_exempt
def upload_weekly_stats(week_number):
    matchups = Schedule.objects.filter(week=week_number).select_related('hometeam', 'awayteam')
    
@csrf_exempt
def upload_stats(request):
    if request.method == 'POST':
        print(request.POST)  # To see what is received in POST
        print(request.FILES)  # To see what files have been received
        try:
            week_number = int(request.POST.get('week'))
            passing_file = request.FILES['passing_file']
            rushing_file = request.FILES['rushing_file']
            receiving_file = request.FILES['receiving_file']
            # Processing files
        except Exception as e:
            print(f"Error: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}")

        try:
            df_passing = pd.read_csv(passing_file)
            df_rushing = pd.read_csv(rushing_file)
            df_receiving = pd.read_csv(receiving_file)
            # df_players = pd.read_csv(players_file)

            # Process these dataframes
            process_weekly_data(df_passing, df_rushing, df_receiving, week_number)
            print("It worked correctly")
        except Exception as e:
            print(f"It did not work: {str(e)}")

    return render(request, 'upload.html')

def process_weekly_data(df_passing, df_rushing, df_receiving, week_number):

    # dfp = df_players[df_players['position'].isin(['QB', 'HB', 'WR', 'TE'])][['rosterId', 'isActive', 'position']]
    # dfp = dfp.rename(columns={"rosterId" : "player__rosterId"})

    # Setting the dataframes to just the player name and their fantasy points
    df_rec = df_receiving[['player__position', 'team__abbrName', 'player__rosterId', 'player__fullName', 'recTotalCatches', 'recTotalYds', 'recTotalTDs']]
    df_rec = df_rec.rename(columns={"player__fullName" : "fullName"})

    df_pass = df_passing[['player__position', 'team__abbrName', 'player__rosterId', 'player__fullName', 'passTotalYds', 'passTotalTDs', 'passTotalInts']]
    df_pass = df_pass.rename(columns={"player__fullName" : "fullName"})

    df_rush = df_rushing[['player__position', 'team__abbrName', 'player__rosterId', 'player__fullName', 'rushTotalYds', 'rushTotalTDs', 'rushTotalFum']]
    df_rush = df_rush.rename(columns={"player__fullName" : "fullName"})
    
    # Start by merging the passing dataframe with the rushing dataframe
    df_combined = pd.merge(df_pass, df_rush, on=['player__position', 'team__abbrName', 'player__rosterId', 'fullName'], how='outer')

    # Now merge the combined dataframe with the receiving dataframe
    df_combined = pd.merge(df_combined, df_rec, on=['player__position', 'team__abbrName', 'player__rosterId', 'fullName'], how='outer')
    df_combined.fillna(0, inplace=True)
    df_combined['fantasyPoints'] = df_combined['recTotalYds'] / 10 + df_combined['recTotalTDs'] * 6 + df_combined['recTotalCatches'] + df_combined['passTotalYds'] / 25 + df_combined['passTotalTDs'] * 4 - df_combined['passTotalInts'] * 2 + df_combined['rushTotalYds'] / 10 + df_combined['rushTotalTDs'] * 6 - df_combined['rushTotalFum'] * 2
    
    print(df_combined)

    # Update database
    for _, row in df_combined.iterrows():
        print(f"Player Roster ID: {row['player__rosterId']}")
        print(f"Full Name: {row['fullName']}")
        print(f"Position: {row['player__position']}")

        try:
            player = Player.objects.get(rosterId=row['player__rosterId'])

            # Default values for stats
            passing_yards = row.get('passTotalYds', 0)
            rushing_yards = row.get('rushTotalYds', 0)
            receiving_yards = row.get('recTotalYds', 0)
            passing_tds = row.get('passTotalTDs', 0)
            rushing_tds = row.get('rushTotalTDs', 0)
            receiving_tds = row.get('recTotalTDs', 0)
            receptions = row.get('recTotalCatches', 0)

            # Check if all stat values are zero
            if (passing_yards == 0 and rushing_yards == 0 and receiving_yards == 0 and
                passing_tds == 0 and rushing_tds == 0 and receiving_tds == 0 and
                receptions == 0):
                fantasy_points = 0.0
            else:
                fantasy_points = row.get('fantasyPoints', 0)

            WeeklyStat.objects.update_or_create(
                player=player,
                week=int(week_number),
                defaults={
                    'passing_yards': passing_yards,
                    'rushing_yards': rushing_yards,
                    'receiving_yards': receiving_yards,
                    'passing_tds': passing_tds,
                    'rushing_tds': rushing_tds,
                    'receiving_tds': receiving_tds,
                    'receptions': receptions,
                    'fantasy_points': fantasy_points
                }
            )
        except Exception as e:
            print(f"Update failed for {row['player__rosterId']} with error: {str(e)}")
            print(f"Values passed: {row.to_dict()}")
            continue

@csrf_exempt
def season_totals(request):
    weeks = range(1, 18)  # Assuming NFL weeks 1 through 15

    # Gather top scorers for each position in each week
    top_scorer_positions = ['QB', 'HB', 'WR', 'TE']
    season_totals = {pos: {} for pos in top_scorer_positions}

    for week in weeks:
        weekly_stats = WeeklyStat.objects.filter(week=week).select_related('player').order_by('player__position', '-fantasy_points')
        week_top_scorers = {pos: [] for pos in top_scorer_positions}

        for stat in weekly_stats:
            position = stat.player.position
            if position in week_top_scorers:
                week_top_scorers[position].append(stat)
                if stat.player.id not in season_totals[position]:
                    season_totals[position][stat.player.id] = {
                        'player': stat.player,
                        'total_points': 0
                    }
                season_totals[position][stat.player.id]['total_points'] += stat.fantasy_points

    # Convert season_totals to a list of dictionaries for easier template parsing
    sorted_season_totals = {}
    for pos, players in season_totals.items():
        sorted_season_totals[pos] = sorted(players.values(), key=lambda x: x['total_points'], reverse=True)[:30]

    return render(request, 'season_totals.html', {'season_totals': sorted_season_totals})
