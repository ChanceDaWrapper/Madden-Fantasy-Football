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
]