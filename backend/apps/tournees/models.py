"""Modèles des tournées et étapes ordonnées (contrat partagé — Larue)."""

from django.db import models
from apps.flotte.models import Livreur, Vehicule
from apps.reseau.models import PointRoutier, TronconRoutier


class CritereOptimisation(models.TextChoices):
    DISTANCE = "distance", "Distance minimale (km)"
    TEMPS = "temps", "Temps estimé minimal (min)"
    COUT = "cout", "Coût pondéré minimal (FCFA)"


class StatutTournee(models.TextChoices):
    PLANIFIEE = "planifiee", "Planifiée"
    EN_COURS = "en_cours", "En cours"
    TERMINEE = "terminee", "Terminée"
    ANNULEE = "annulee", "Annulée"


class Tournee(models.Model):
    """Tournée de livraison planifiée pour un véhicule et un livreur."""

    date = models.DateField("date de tournée")
    point_depart = models.ForeignKey(
        PointRoutier,
        on_delete=models.PROTECT,
        related_name="tournees_depart",
        verbose_name="point de départ",
    )
    vehicule = models.ForeignKey(
        Vehicule,
        on_delete=models.PROTECT,
        related_name="tournees",
        verbose_name="véhicule",
    )
    livreur = models.ForeignKey(
        Livreur,
        on_delete=models.PROTECT,
        related_name="tournees",
        verbose_name="livreur",
    )
    critere = models.CharField(
        "critère d'optimisation",
        max_length=20,
        choices=CritereOptimisation.choices,
        default=CritereOptimisation.DISTANCE,
    )
    statut = models.CharField(
        "statut",
        max_length=20,
        choices=StatutTournee.choices,
        default=StatutTournee.PLANIFIEE,
    )
    distance_totale_km = models.FloatField("distance totale (km)", default=0.0)
    temps_total_min = models.FloatField("temps total estimé (min)", default=0.0)
    cout_total_fcfa = models.FloatField("coût total estimé (FCFA)", default=0.0)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tournée"
        verbose_name_plural = "Tournées"
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["livreur", "date"], name="tournee_livreur_date_idx"),
        ]

    def __str__(self) -> str:
        return f"Tournée #{self.pk} — {self.date} ({self.livreur.nom})"


class EtapeTournee(models.Model):
    """Étape ordonnée d'une tournée avec valeurs cumulées."""

    tournee = models.ForeignKey(
        Tournee,
        on_delete=models.CASCADE,
        related_name="etapes",
        verbose_name="tournée",
    )
    rang = models.PositiveIntegerField("rang")
    point_routier = models.ForeignKey(
        PointRoutier,
        on_delete=models.PROTECT,
        related_name="etapes_tournees",
        verbose_name="point routier",
    )
    troncon = models.ForeignKey(
        TronconRoutier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="etapes_tournees",
        verbose_name="tronçon emprunté",
    )
    distance_cumulee_km = models.FloatField("distance cumulée (km)", default=0.0)
    temps_cumule_min = models.FloatField("temps cumulé (min)", default=0.0)
    cout_cumule_fcfa = models.FloatField("coût cumulé (FCFA)", default=0.0)

    class Meta:
        verbose_name = "Étape de tournée"
        verbose_name_plural = "Étapes de tournée"
        ordering = ["tournee_id", "rang"]
        constraints = [
            models.UniqueConstraint(
                fields=["tournee", "rang"],
                name="etape_tournee_rang_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"Tournée #{self.tournee_id} — Étape {self.rang} ({self.point_routier.nom})"
