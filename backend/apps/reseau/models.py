"""Modèles du réseau routier simplifié et fictif (contrat partagé — Serena)."""

from django.core.exceptions import ValidationError
from django.db import models


class NiveauCongestion(models.TextChoices):
    FLUIDE = "fluide", "Fluide"
    MODEREE = "moderee", "Modérée"
    FORTE = "forte", "Forte"


class EtatRoute(models.TextChoices):
    BON = "bon", "Bon état"
    DEGRADE = "degrade", "Dégradé"
    TRES_DEGRADE = "tres_degrade", "Très dégradé"
    IMPRATICABLE = "impraticable", "Impraticable"


class PointRoutier(models.Model):
    """Nœud du graphe routier fictif inspiré des quartiers de Douala."""

    nom = models.CharField("nom du point", max_length=120, unique=True)
    quartier = models.CharField("quartier", max_length=120)
    repere = models.CharField("point de repère", max_length=200, blank=True)
    x = models.FloatField("coordonnée X fictive", default=0.0)
    y = models.FloatField("coordonnée Y fictive", default=0.0)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Point routier"
        verbose_name_plural = "Points routiers"
        ordering = ["nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.quartier})"


class TronconRoutier(models.Model):
    """Arc orienté reliant deux points routiers (double_sens crée l'arc inverse)."""

    origine = models.ForeignKey(
        PointRoutier,
        on_delete=models.CASCADE,
        related_name="troncons_sortants",
        verbose_name="point d'origine",
    )
    destination = models.ForeignKey(
        PointRoutier,
        on_delete=models.CASCADE,
        related_name="troncons_entrants",
        verbose_name="point de destination",
    )
    distance_km = models.FloatField("distance (km)")
    duree_base_min = models.FloatField("durée de base (min)")
    congestion = models.CharField(
        "congestion",
        max_length=20,
        choices=NiveauCongestion.choices,
        default=NiveauCongestion.FLUIDE,
    )
    etat_route = models.CharField(
        "état de la route",
        max_length=20,
        choices=EtatRoute.choices,
        default=EtatRoute.BON,
    )
    praticable_moto = models.BooleanField("praticable à moto", default=True)
    praticable_vehicule_leger = models.BooleanField(
        "praticable en véhicule léger",
        default=True,
    )
    double_sens = models.BooleanField("double sens", default=True)
    est_ferme = models.BooleanField("tronçon fermé", default=False)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tronçon routier"
        verbose_name_plural = "Tronçons routiers"
        ordering = ["origine__nom", "destination__nom"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(distance_km__gt=0),
                name="troncon_distance_gt_0",
            ),
            models.CheckConstraint(
                condition=models.Q(duree_base_min__gt=0),
                name="troncon_duree_gt_0",
            ),
            models.CheckConstraint(
                condition=~models.Q(origine=models.F("destination")),
                name="troncon_origine_diff_destination",
            ),
        ]

    def clean(self) -> None:
        errors = {}
        if self.origine_id and self.destination_id and self.origine_id == self.destination_id:
            errors["destination"] = "L'origine et la destination doivent être distinctes."
        if self.distance_km is not None and self.distance_km <= 0:
            errors["distance_km"] = "La distance doit être strictement positive."
        if self.duree_base_min is not None and self.duree_base_min <= 0:
            errors["duree_base_min"] = "La durée de base doit être strictement positive."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        fleche = "<->" if self.double_sens else "->"
        return f"{self.origine.nom} {fleche} {self.destination.nom} ({self.distance_km} km)"
