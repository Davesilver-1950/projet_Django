"""Sérialiseurs JWT et profil utilisateur (socle minimal pour Sandra)."""

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import RoleUtilisateur, Utilisateur
from apps.flotte.models import Livreur


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


class UtilisateurSerializer(serializers.ModelSerializer):
    """CRUD des comptes (réservé à l'Administrateur).

    Le mot de passe est en écriture seule : il n'est jamais renvoyé par l'API.
    Pour un compte livreur, nom et telephone_fictif servent à créer le profil Livreur.
    """

    role_libelle = serializers.CharField(source="get_role_display", read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    nom = serializers.CharField(write_only=True, required=False, max_length=120)
    telephone_fictif = serializers.CharField(write_only=True, required=False, max_length=30)

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
            "password",
            "nom",
            "telephone_fictif",
        ]
        read_only_fields = ["id", "role_libelle"]

    def validate(self, attrs):
        creation = self.instance is None
        if creation and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Le mot de passe est obligatoire."})
        if attrs.get("password"):
            validate_password(attrs["password"], user=self.instance)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        nom = validated_data.pop("nom", None)
        telephone = validated_data.pop("telephone_fictif", "")
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        self._assurer_profil_livreur(user, nom, telephone)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        nom = validated_data.pop("nom", None)
        telephone = validated_data.pop("telephone_fictif", None)
        for champ, valeur in validated_data.items():
            setattr(instance, champ, valeur)
        if password:
            instance.set_password(password)
        instance.save()
        self._assurer_profil_livreur(instance, nom, telephone)
        return instance

    @staticmethod
    def _assurer_profil_livreur(user, nom, telephone):
        """Crée le profil Livreur s'il manque ; un profil existant n'est pas modifié."""
        if user.role != RoleUtilisateur.LIVREUR:
            return
        Livreur.objects.get_or_create(
            utilisateur=user,
            defaults={
                "nom": nom or user.get_full_name() or user.username,
                "telephone_fictif": telephone or "000000000",
            },
        )