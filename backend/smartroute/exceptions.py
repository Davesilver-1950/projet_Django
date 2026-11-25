"""Gestionnaire d'exceptions DRF uniforme : {"code", "message", "details"}."""

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Formate toutes les erreurs API au format uniforme {"code", "message", "details"}."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    code = "ERREUR_API"
    message = "Une erreur est survenue lors du traitement de la requête."
    details = response.data

    if isinstance(exc, NotAuthenticated):
        code = "NON_AUTHENTIFIE"
        message = "Authentification requise pour accéder à cette ressource."
    elif isinstance(exc, AuthenticationFailed):
        code = "IDENTIFIANTS_INVALIDES"
        message = "Identifiants invalides ou jeton d'accès expiré."
    elif isinstance(exc, PermissionDenied):
        code = "ACCES_INTERDIT"
        message = "Vous n'avez pas les permissions nécessaires pour cette action."
    elif isinstance(exc, NotFound):
        code = "RESSOURCE_INTROUVABLE"
        message = "La ressource demandée est introuvable."
    elif isinstance(exc, ValidationError):
        code = "DONNEES_INVALIDES"
        message = "Les données fournies sont invalides."
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        code = "REQUETE_INVALIDE"
        message = "Requête invalide."
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = "RESSOURCE_INTROUVABLE"
        message = "Ressource introuvable."

    if isinstance(response.data, dict) and "detail" in response.data and len(response.data) == 1:
        details = {"detail": str(response.data["detail"])}

    response.data = {
        "code": code,
        "message": message,
        "details": details,
    }
    return response
