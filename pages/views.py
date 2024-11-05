# pages/views.py
from django.http import HttpResponse, JsonResponse, Http404
import json, random
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from teams.models import Team, Player, WeeklyStat, Position, Schedule
from django.db.models import Prefetch
import pandas as pd

team_ids_ordered = list(Team.objects.order_by('id').values_list('id', flat=True)) # Assuming team_ids_ordered is a list of team IDs in draft order

current_team_index = 0 # Current team's index in team_ids_ordered
draft_direction = 1 # Draft direction: 1 for forward, -1 for backward

round_1_plus = False # Initial round variable
positions_global = None # Global positions variable for display in drafting.html

draft_list = [] # Total drafted list
round_counter = 1
pick_counter = 1

class HomePageView(TemplateView):
    print()
    template_name = 'home.html'
    
def playerData(request):
    global current_team_index, draft_direction, team_ids_ordered, round_1_plus, draft_list
    current_team_id = team_ids_ordered[current_team_index]
    positions = Position.objects.filter(team_id=current_team_id)

    # Fetch all players from the database
    players = Player.objects.all().order_by('-lastSeasonPts')
    team = Team.objects.get(id=current_team_id)
    team_name = team.name
    if not round_1_plus:
        draft_direction = 1
        # If there are no positions yet, we initialize the setup
        initial_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'RQB', 'RRB', 'RWR', 'RTE']
        positions = [{'position': pos, 'player': None} for pos in initial_positions]
    else: 
        positions = positions_global
    
    print("\n\nGetting to last bit\n\n")
    return render(request, 'drafting.html', {'players' : players, 'positions' : positions, 'fantasy_team' : team_name, 'draft_list' : draft_list })



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


@csrf_exempt  # Use this decorator to exempt this view from CSRF verification.
@require_http_methods(["POST"])  # Ensure that this view only accepts POST requests.
def draft_player(request):
    global current_team_index, draft_direction, team_ids_ordered, round_1_plus, positions_global, draft_list, pick_counter, round_counter
    print(team_ids_ordered)
            
    
    # Parse the JSON data from the request body
    try:
        data = json.loads(request.body)
        player_id = data['playerId']
        position = data.get('universalSpot')  # Assuming you also send position in your request

        current_team_id = team_ids_ordered[current_team_index]
        team = Team.objects.get(id=current_team_id)
    
        # Draft the player
        player = Player.objects.get(id=player_id)
        team.draft_player(player, position) # Method to draft the player to the team
        player.drafted = True # Set the player's drafted status to true
        player.save() # Saving the player instance

        str1 = f"{round_counter}.{pick_counter}: {team.name} -- {player.position} {player}"
        draft_list.append(str1)
        pick_counter += 1
        current_team_index += draft_direction
        
        
        # Check if we have reached the end or the beginning of the list to reverse the direction
        if current_team_index >= len(team_ids_ordered) or current_team_index < 0:
            draft_direction *= -1  # Reverse the direction
            # Ensure current_team_index stays within bounds
            current_team_index = max(0, min(current_team_index, len(team_ids_ordered) - 1))
            round_1_plus = True
            pick_counter = 1
            round_counter += 1
        
        current_team_id = team_ids_ordered[current_team_index]
        initial_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'RQB', 'RRB', 'RWR', 'RTE']
        positions_with_none = [{'position': pos, 'player': None} for pos in initial_positions]
        # Assuming you have a queryset of filled positions from your database
        filled_positions = Position.objects.filter(team_id=current_team_id).select_related('player')

        # Convert filled_positions to a dictionary for efficient lookups
        filled_positions_dict = {pos.position: pos.player for pos in filled_positions}

        # Update positions_with_none with players from filled_positions where applicable
        for position in positions_with_none:
            if position['position'] in filled_positions_dict:
                playerSwap = filled_positions_dict[position['position']]
                position['player'] = playerSwap.name if playerSwap else None
        
        
        positions_global = positions_with_none
        
        return redirect('Drafting')
        
    except json.JSONDecodeError:
        # If there's an error in parsing JSON
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data received.'}, status=400)
    except KeyError:
        # If the expected key ('playerId') is not found in the data
        return JsonResponse({'status': 'error', 'message': 'Missing playerId in data.'}, status=400)
    except Exception as e:
        # General exception handler (optional, but good for catching unexpected errors)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
def reset_players(request):
    global team_ids_ordered, positions_global, round_1_plus, draft_list, pick_counter, round_counter
    positions_global = None
    round_1_plus = False
    draft_list = []
    pick_counter = 1
    round_counter = 1
    team_ids_ordered = list(Team.objects.order_by('id').values_list('id', flat=True))

    random.shuffle(team_ids_ordered)
    for i in team_ids_ordered:
        team = Team.objects.get(id=i)
        print(team.name)
    print("\n\n", team_ids_ordered, "\n\n")
    try:
        # Delete all position instances, effectively detaching players from teams
        Position.objects.all().delete()
        Player.objects.update(drafted=False)
        return redirect("team_create")
    except Exception as e:
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



@csrf_exempt
def matchups(request):
    weeks = range(1, 15)  # Assuming NFL weeks 1 through 17
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
            matchup.hometeam.points = hometeam_points
            matchup.awayteam.points = awayteam_points
            
            # Add winner/loser class based on points
            if hometeam_points > awayteam_points:
                matchup.hometeam.result_class = 'winner'
                matchup.awayteam.result_class = 'loser'
            elif hometeam_points < awayteam_points:
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
