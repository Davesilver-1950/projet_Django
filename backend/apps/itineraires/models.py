"""Modèle CalculItineraire pour l'historique et la comparaison avant/après (EF-15)."""

from django.conf import settings
from django.db import models
from apps.flotte.models import TypeVehicule
from apps.reseau.models import PointRoutier
from apps.tournees.models import CritereOptimisation


class CalculItineraire(models.Model):
    """Instantané d'un calcul d'itinéraire conservé pour comparaison avant/après."""

    libelle = models.CharField("libellé du scénario", max_length=160, blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calculs_itineraires",
        verbose_name="calculé par",
    )
    origine = models.ForeignKey(
        PointRoutier,
        on_delete=models.PROTECT,
        related_name="calculs_origine",
        verbose_name="point de départ",
    )
    destination = models.ForeignKey(
        PointRoutier,
        on_delete=models.PROTECT,
        related_name="calculs_destination",
        verbose_name="point d'arrivée",
    )
    points_demandes = models.JSONField("ordre des points demandés", default=list)
    type_vehicule = models.CharField(
        "type de véhicule",
        max_length=20,
        choices=TypeVehicule.choices,
    )
    critere = models.CharField(
        "critère d'optimisation",
        max_length=20,
        choices=CritereOptimisation.choices,
    )
    distance_totale_km = models.FloatField("distance totale (km)")
    temps_total_min = models.FloatField("temps total estimé (min)")
    cout_total_fcfa = models.FloatField("coût total estimé (FCFA)")
    etapes_snapshot = models.JSONField("instantané des étapes", default=list)
    hypotheses_snapshot = models.JSONField("instantané des hypothèses", default=dict)
    donnees_fictives = models.BooleanField("données fictives", default=True)
    cree_le = models.DateTimeField("calculé le", auto_now_add=True)

    class Meta:
        verbose_name = "Calcul d'itinéraire"
        verbose_name_plural = "Calculs d'itinéraires"
        ordering = ["-cree_le", "-id"]

    def __str__(self) -> str:
        titre = self.libelle or f"{self.origine.nom} -> {self.destination.nom}"
        return f"Calcul #{self.pk} — {titre} ({self.critere})"
