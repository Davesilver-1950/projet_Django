"""Vues d'authentification JWT et gestion des comptes (Administrateur uniquement)."""

from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import Utilisateur
from apps.accounts.permissions import IsAdministrateur
from apps.accounts.serializers import (
    SmartRouteTokenObtainPairSerializer,
    UtilisateurProfilSerializer,
    UtilisateurSerializer,
)


class ConnexionJWTView(TokenObtainPairView):
    """Authentification JWT (EF-01). Identifiants invalides ou compte inactif -> 401."""

    serializer_class = SmartRouteTokenObtainPairSerializer


class RafraichirJWTView(TokenRefreshView):
    """Renouvellement du jeton d'accès JWT."""


class ProfilCourantView(APIView):
    """Retourne le profil de l'utilisateur authentifié."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UtilisateurProfilSerializer(request.user).data)


class UtilisateurViewSet(ModelViewSet):
    """CRUD des comptes. Réservé à l'Administrateur (401 sans jeton, 403 sinon)."""

    queryset = Utilisateur.objects.all().order_by("username")
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAdministrateur]

    def perform_update(self, serializer):
        # Un administrateur ne peut pas se retirer ses propres droits ni se désactiver.
        if serializer.instance.pk == self.request.user.pk:
            donnees = serializer.validated_data
            if donnees.get("role", serializer.instance.role) != serializer.instance.role or (
                donnees.get("is_active", True) is False
            ):
                raise PermissionDenied(
                    "Vous ne pouvez pas modifier votre propre rôle ni désactiver votre compte."
                )
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        compte = self.get_object()
        if compte.pk == request.user.pk:
            raise PermissionDenied("Vous ne pouvez pas supprimer votre propre compte.")
        try:
            compte.delete()
        except ProtectedError:
            return Response(
                {
                    "code": "SUPPRESSION_IMPOSSIBLE",
                    "message": "Ce compte est lié à des tournées : désactivez-le au lieu de le supprimer.",
                    "details": {},
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)