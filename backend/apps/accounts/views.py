"""Vues JWT de base (/api/auth/login/, /refresh/, /me/)."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.serializers import (
    SmartRouteTokenObtainPairSerializer,
    UtilisateurProfilSerializer,
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
