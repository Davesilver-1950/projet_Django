"""Enregistrement admin des calculs d'itinéraires."""

from django.contrib import admin
from apps.itineraires.models import CalculItineraire


@admin.register(CalculItineraire)
class CalculItineraireAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "libelle",
        "origine",
        "destination",
        "type_vehicule",
        "critere",
        "distance_totale_km",
        "temps_total_min",
        "cout_total_fcfa",
        "cree_le",
    )
    list_filter = ("type_vehicule", "critere", "donnees_fictives")
