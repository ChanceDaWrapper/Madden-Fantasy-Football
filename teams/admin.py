# teams/admin.py

# admin.py in your app directory
from django.contrib import admin
from .models import Player, Team

admin.site.register(Player)
admin.site.register(Team)