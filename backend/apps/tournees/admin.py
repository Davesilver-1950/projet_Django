"""Administration des tournées."""

from django.contrib import admin
from apps.tournees.models import EtapeTournee, Tournee

admin.site.register(Tournee)
admin.site.register(EtapeTournee)
