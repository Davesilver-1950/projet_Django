"""Routes d'authentification (Sandra ajoutera CRUD utilisateurs et T3)."""

from django.urls import path
from apps.accounts.views import ConnexionJWTView, ProfilCourantView, RafraichirJWTView

app_name = "accounts"

urlpatterns = [
    path("login/", ConnexionJWTView.as_view(), name="token-obtain-pair"),
    path("refresh/", RafraichirJWTView.as_view(), name="token-refresh"),
    path("me/", ProfilCourantView.as_view(), name="profil-courant"),
]
