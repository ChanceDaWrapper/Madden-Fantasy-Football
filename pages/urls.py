# pages/urls.py
from django.urls import path # Importing from django to power the URL pattern

from .views import HomePageView, playerData, teamCreate # Importing from views
from . import views

urlpatterns = [
    path('', HomePageView.as_view(), name='Home'),
    path('draft', views.playerData, name='Drafting'),
    path('team_create', views.teamCreate, name='team_create'),
    path('delete_team/<int:team_id>/', views.deleteTeam, name='delete_team'),
    path('draft_player', views.draft_player, name='draft_player'),
    path('reset_players', views.reset_players, name='reset_players'),
    path('rosters', views.rosters, name='Rosters'),
    path('matchups', views.matchups, name='Matchups'),
    path('generate_schedule', views.generate_schedule, name='generate_schedule'),
    path('upload_stats', views.upload_stats, name='upload_stats'), 
    path('upload-weekly-stats', views.upload_weekly_stats, name='upload_weekly_stats'),
    path('season-totals', views.season_totals, name='season_totals'),
    path('records', views.records, name='Records')
]