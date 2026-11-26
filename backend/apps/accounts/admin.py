"""Enregistrement admin des utilisateurs."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rôle SmartRoute CM", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active")
