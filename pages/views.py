# pages/views.py
from django.http import HttpResponse, JsonResponse
import json, random
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from teams.models import Team, Player, WeeklyStat, Position

# Assuming team_ids_ordered is a list of team IDs in draft order
team_ids_ordered = list(Team.objects.order_by('id').values_list('id', flat=True))
# Current team's index in team_ids_ordered
current_team_index = 0
# Draft direction: 1 for forward, -1 for backward
draft_direction = 1

round_1_plus = False
positions_global = None

draft_list = []

class HomePageView(TemplateView):
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
    team = Team.objects.get(id=team_id)
    team.delete()
    return redirect('team_create')


@csrf_exempt  # Use this decorator to exempt this view from CSRF verification.
@require_http_methods(["POST"])  # Ensure that this view only accepts POST requests.
def draft_player(request):
    global current_team_index, draft_direction, team_ids_ordered, round_1_plus, positions_global, draft_list
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
        
        # Print statements to make sure they are attached correctly
        print("\n\n")
        print(player, " has been drafted to ", team.name,"'s team")
        print("\n\n")
        
        str1 = f"{team.name} -- {player.position} {player}"
        draft_list.append(str1)
        
        current_team_index += draft_direction
        
        # Check if we have reached the end or the beginning of the list to reverse the direction
        if current_team_index >= len(team_ids_ordered) or current_team_index < 0:
            draft_direction *= -1  # Reverse the direction
            # Ensure current_team_index stays within bounds
            current_team_index = max(0, min(current_team_index, len(team_ids_ordered) - 1))
            print("\n\nSwitching Direction\n\n")
            round_1_plus = True
        
        current_team_id = team_ids_ordered[current_team_index]
        print("\n\n Starting the positions adjustment")
        initial_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'RQB', 'RRB', 'RWR', 'RTE']
        positions_with_none = [{'position': pos, 'player': None} for pos in initial_positions]
        # Assuming you have a queryset of filled positions from your database
        # For example, filled_positions = Position.objects.filter(team_id=current_team_id).select_related('player')
        filled_positions = Position.objects.filter(team_id=current_team_id).select_related('player')

        # Convert filled_positions to a dictionary for efficient lookups
        filled_positions_dict = {pos.position: pos.player for pos in filled_positions}

        # Update positions_with_none with players from filled_positions where applicable
        for position in positions_with_none:
            if position['position'] in filled_positions_dict:
                playerSwap = filled_positions_dict[position['position']]
                position['player'] = playerSwap.name if playerSwap else None
        
        print("\n\n")
        
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
    global team_ids_ordered, positions_global, round_1_plus, draft_list
    positions_global = None
    round_1_plus = False
    draft_list = []
    team_ids_ordered = list(Team.objects.order_by('id').values_list('id', flat=True))

    random.shuffle(team_ids_ordered)
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
        positions = Position.objects.filter(team=team)
        team_rosters[team] = positions

    return render(request, 'rosters.html', {'team_rosters': team_rosters})