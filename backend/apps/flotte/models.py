"""Modèles flotte, points de livraison et colis (contrat partagé — Daphné)."""

from django.conf import settings
from django.db import models
from apps.reseau.models import PointRoutier


class TypeVehicule(models.TextChoices):
    MOTO = "moto", "Moto"
    VEHICULE_LEGER = "vehicule_leger", "Véhicule léger"


class StatutColis(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    PLANIFIE = "planifie", "Planifié"
    EN_COURS = "en_cours", "En cours"
    LIVRE = "livre", "Livré"


class Livreur(models.Model):
    """Profil livreur lié à un compte utilisateur (données fictives)."""

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_livreur",
        verbose_name="compte utilisateur",
    )
    nom = models.CharField("nom complet fictif", max_length=120)
    telephone_fictif = models.CharField("téléphone fictif", max_length=30)
    disponible = models.BooleanField("disponible", default=True)

    class Meta:
        verbose_name = "Livreur"
        verbose_name_plural = "Livreurs"
        ordering = ["nom"]

    def __str__(self) -> str:
        return self.nom


class Vehicule(models.Model):
    """Véhicule de livraison avec type et capacité maximale en kg."""

    immatriculation_fictif = models.CharField(
        "immatriculation fictive",
        max_length=30,
        unique=True,
    )
    type_vehicule = models.CharField(
        "type de véhicule",
        max_length=20,
        choices=TypeVehicule.choices,
    )
    capacite_kg = models.FloatField("capacité maximale (kg)")

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ["immatriculation_fictif"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacite_kg__gt=0),
                name="vehicule_capacite_gt_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.immatriculation_fictif} ({self.get_type_vehicule_display()})"


class PointLivraison(models.Model):
    """Point de livraison rattaché à un nœud du graphe routier."""

    destinataire_fictif = models.CharField("destinataire fictif", max_length=120)
    quartier = models.CharField("quartier", max_length=120)
    repere = models.CharField("point de repère", max_length=200)
    point_routier = models.ForeignKey(
        PointRoutier,
        on_delete=models.PROTECT,
        related_name="points_livraison",
        verbose_name="point routier associé",
    )

    class Meta:
        verbose_name = "Point de livraison"
        verbose_name_plural = "Points de livraison"
        ordering = ["quartier", "destinataire_fictif"]

    def __str__(self) -> str:
        return f"{self.destinataire_fictif} — {self.quartier} ({self.repere})"


class Colis(models.Model):
    """Colis fictif à livrer sur un point de livraison."""

    reference = models.CharField("référence", max_length=50, unique=True)
    poids_kg = models.FloatField("poids (kg)")
    statut = models.CharField(
        "statut",
        max_length=20,
        choices=StatutColis.choices,
        default=StatutColis.EN_ATTENTE,
    )
    point_livraison = models.ForeignKey(
        PointLivraison,
        on_delete=models.PROTECT,
        related_name="colis",
        verbose_name="point de livraison",
    )

    class Meta:
        verbose_name = "Colis"
        verbose_name_plural = "Colis"
        ordering = ["reference"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(poids_kg__gt=0),
                name="colis_poids_gt_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reference} ({self.poids_kg} kg)"
