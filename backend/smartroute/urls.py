"""Configuration des URLs principales de SmartRoute CM."""

from django.contrib import admin
from django.urls import path
from smartroute.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
]
