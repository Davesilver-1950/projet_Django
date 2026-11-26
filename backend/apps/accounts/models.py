"""Modèle Utilisateur personnalisé avec rôles métier SmartRoute CM."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class RoleUtilisateur(models.TextChoices):
    """Rôles définis dans le cahier des charges (section 2)."""

    ADMIN = "admin", "Administrateur"
    GESTIONNAIRE = "gestionnaire", "Gestionnaire logistique"
    LIVREUR = "livreur", "Livreur"


class Utilisateur(AbstractUser):
    """Utilisateur authentifié par JWT avec contrôle d'accès basé sur le rôle."""

    email = models.EmailField("adresse e-mail", unique=True)
    role = models.CharField(
        "rôle",
        max_length=20,
        choices=RoleUtilisateur.choices,
        default=RoleUtilisateur.LIVREUR,
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
