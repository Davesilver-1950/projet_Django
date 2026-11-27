"""Routes d'authentification et de gestion des comptes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    ConnexionJWTView,
    ProfilCourantView,
    RafraichirJWTView,
    UtilisateurViewSet,
)

app_name = "accounts"

router = DefaultRouter()
router.register("utilisateurs", UtilisateurViewSet, basename="utilisateur")

urlpatterns = [
    path("login/", ConnexionJWTView.as_view(), name="token-obtain-pair"),
    path("refresh/", RafraichirJWTView.as_view(), name="token-refresh"),
    path("me/", ProfilCourantView.as_view(), name="profil-courant"),
    path("", include(router.urls)),
]