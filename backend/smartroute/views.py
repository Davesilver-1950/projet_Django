"""Vues transverses de l'API SmartRoute CM."""

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@csrf_exempt
def api_route_introuvable(request):
    """404 JSON au format uniforme pour toute URL inconnue sous /api/ (ENF-04)."""
    return JsonResponse(
        {
            "code": "RESSOURCE_INTROUVABLE",
            "message": "La ressource demandée est introuvable.",
            "details": {"chemin": request.path},
        },
        status=404,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint de santé public (/api/health/) vérifiant l'API et la base de données."""
    db_status = "ok"
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except OperationalError:
        db_status = "error"

    return Response(
        {
            "status": "ok" if db_status == "ok" else "degraded",
            "service": "SmartRoute CM API",
            "version": "0.1.0",
            "database": db_status,
            "donnees_fictives": True,
        }
    )
