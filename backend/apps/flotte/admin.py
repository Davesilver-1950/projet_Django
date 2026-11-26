"""Administration de la flotte et des colis."""

from django.contrib import admin
from apps.flotte.models import Colis, Livreur, PointLivraison, Vehicule

admin.site.register(Livreur)
admin.site.register(Vehicule)
admin.site.register(PointLivraison)
admin.site.register(Colis)
