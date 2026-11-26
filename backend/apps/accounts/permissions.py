"""Permissions DRF par rôle (401 si non authentifié, 403 si rôle insuffisant)."""

from rest_framework.permissions import BasePermission
from apps.accounts.models import RoleUtilisateur


class _HasRole(BasePermission):
    """Classe de base vérifiant que l'utilisateur actif possède un rôle autorisé."""

    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role in self.allowed_roles
        )


class IsAdministrateur(_HasRole):
    """Autorise uniquement les comptes Administrateur."""

    allowed_roles = (RoleUtilisateur.ADMIN,)


class IsGestionnaire(_HasRole):
    """Autorise uniquement les comptes Gestionnaire logistique."""

    allowed_roles = (RoleUtilisateur.GESTIONNAIRE,)


class IsLivreur(_HasRole):
    """Autorise uniquement les comptes Livreur."""

    allowed_roles = (RoleUtilisateur.LIVREUR,)


class IsAdminOrGestionnaire(_HasRole):
    """Autorise Administrateur et Gestionnaire logistique."""

    allowed_roles = (RoleUtilisateur.ADMIN, RoleUtilisateur.GESTIONNAIRE)
