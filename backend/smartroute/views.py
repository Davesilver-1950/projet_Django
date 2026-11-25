"""Vues transverses de l'API SmartRoute CM."""

from django.db import connections
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


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
