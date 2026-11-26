"""Configuration des URLs principales de SmartRoute CM."""

from django.contrib import admin
from django.urls import include, path
from smartroute.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/reseau/", include("apps.reseau.urls")),
    path("api/flotte/", include("apps.flotte.urls")),
    path("api/tournees/", include("apps.tournees.urls")),
    path("api/itineraires/", include("apps.itineraires.urls")),
]
