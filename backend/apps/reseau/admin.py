"""Administration du réseau routier."""

from django.contrib import admin
from apps.reseau.models import PointRoutier, TronconRoutier


@admin.register(PointRoutier)
class PointRoutierAdmin(admin.ModelAdmin):
    list_display = ("nom", "quartier", "repere", "x", "y")
    search_fields = ("nom", "quartier")


@admin.register(TronconRoutier)
class TronconRoutierAdmin(admin.ModelAdmin):
    list_display = (
        "origine",
        "destination",
        "distance_km",
        "duree_base_min",
        "congestion",
        "etat_route",
        "double_sens",
        "est_ferme",
    )
    list_filter = ("congestion", "etat_route", "est_ferme", "double_sens")
