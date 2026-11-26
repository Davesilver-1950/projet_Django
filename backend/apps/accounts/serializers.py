"""Sérialiseurs JWT et profil utilisateur (socle minimal pour Sandra)."""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import Utilisateur


class UtilisateurProfilSerializer(serializers.ModelSerializer):
    """Représentation publique d'un utilisateur connecté."""

    role_libelle = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_libelle",
            "is_active",
        ]
        read_only_fields = fields


class SmartRouteTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Enrichit la réponse JWT avec les informations du profil utilisateur."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UtilisateurProfilSerializer(self.user).data
        return data
