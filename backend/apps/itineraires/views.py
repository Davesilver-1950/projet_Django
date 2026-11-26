"""Vues API REST du module itinéraires (calcul, comparaison, historique, pondération)."""

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminOrGestionnaire, IsGestionnaire
from apps.flotte.models import TypeVehicule
from apps.itineraires.models import CalculItineraire
from apps.itineraires.ponderation import get_hypotheses_ponderation
from apps.itineraires.serializers import (
    CalculItineraireHistoriqueSerializer,
    CalculItineraireRequeteSerializer,
    PointRoutierSimpleSerializer,
    resoudre_points_ordonnes,
)
from apps.itineraires.services import (
    calculer_et_sauvegarder_itineraire,
    comparer_avant_apres,
    comparer_trois_criteres,
)
from apps.reseau.models import PointRoutier


def _parse_int(value: str | None, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field_name: f"'{field_name}' doit être un entier positif."}) from exc
    if parsed <= 0:
        raise ValidationError({field_name: f"'{field_name}' doit être supérieur à 0."})
    return parsed


def _parse_int_list(raw_values: list[str], field_name: str) -> list[int]:
    resultat: list[int] = []
    for item in raw_values:
        for morceau in str(item).split(","):
            morceau = morceau.strip()
            if not morceau:
                continue
            val = _parse_int(morceau, field_name)
            if val is not None:
                resultat.append(val)
    return resultat


class CalculerItineraireView(APIView):
    """POST /api/itineraires/calculer/ (Gestionnaire uniquement)."""

    permission_classes = [IsGestionnaire]

    def post(self, request):
        serializer = CalculItineraireRequeteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payload = calculer_et_sauvegarder_itineraire(
            points_ids=data["points_ordonnes"],
            type_vehicule=data["type_vehicule"],
            critere=data["critere"],
            user=request.user,
            enregistrer=data["enregistrer"],
            libelle=data["libelle"],
        )
        return Response(payload)


class ComparerItinerairesView(APIView):
    """GET /api/itineraires/comparer/ (Gestionnaire uniquement).

    Deux modes supportés :
    1) Comparaison 3 critères : ?origine_id=...&destination_id=...&type_vehicule=...
    2) Comparaison avant/après : ?calcul_avant_id=...&calcul_apres_id=... (ou &recalculer=true)
    """

    permission_classes = [IsGestionnaire]

    def get(self, request):
        calcul_avant_id = _parse_int(
            request.query_params.get("calcul_avant_id"), "calcul_avant_id"
        )
        if calcul_avant_id is not None:
            calcul_avant = get_object_or_404(CalculItineraire, pk=calcul_avant_id)
            calcul_apres_id = _parse_int(
                request.query_params.get("calcul_apres_id"), "calcul_apres_id"
            )
            calcul_apres = (
                get_object_or_404(CalculItineraire, pk=calcul_apres_id)
                if calcul_apres_id is not None
                else None
            )
            recalculer_raw = request.query_params.get("recalculer", "false").strip().lower()
            recalculer = recalculer_raw in ("1", "true", "yes", "oui") or calcul_apres is None

            payload = comparer_avant_apres(
                calcul_avant=calcul_avant,
                calcul_apres=calcul_apres,
                recalculer=recalculer,
                user=request.user,
            )
            return Response(payload)

        origine_id = _parse_int(request.query_params.get("origine_id"), "origine_id")
        destination_id = _parse_int(request.query_params.get("destination_id"), "destination_id")
        etapes_ids = _parse_int_list(request.query_params.getlist("etapes_ids"), "etapes_ids")
        points_ids = _parse_int_list(request.query_params.getlist("points_ids"), "points_ids")

        points_ordonnes = resoudre_points_ordonnes(
            origine_id=origine_id,
            destination_id=destination_id,
            etapes_ids=etapes_ids,
            points_ids=points_ids or None,
        )

        type_vehicule = request.query_params.get(
            "type_vehicule", TypeVehicule.VEHICULE_LEGER
        ).strip()
        if type_vehicule not in (TypeVehicule.MOTO, TypeVehicule.VEHICULE_LEGER):
            raise ValidationError(
                {
                    "type_vehicule": (
                        f"Type de véhicule invalide : '{type_vehicule}'. "
                        "Valeurs autorisées : moto, vehicule_leger."
                    )
                }
            )

        payload = comparer_trois_criteres(
            points_ids=points_ordonnes,
            type_vehicule=type_vehicule,
        )
        return Response(payload)


class CalculHistoriqueListView(generics.ListAPIView):
    """GET /api/itineraires/calculs/ — historique des calculs enregistrés."""

    permission_classes = [IsAdminOrGestionnaire]
    serializer_class = CalculItineraireHistoriqueSerializer
    queryset = CalculItineraire.objects.select_related("origine", "destination", "cree_par").all()


class CalculHistoriqueDetailView(generics.RetrieveAPIView):
    """GET /api/itineraires/calculs/{id}/ — détail d'un calcul enregistré."""

    permission_classes = [IsAdminOrGestionnaire]
    serializer_class = CalculItineraireHistoriqueSerializer
    queryset = CalculItineraire.objects.select_related("origine", "destination", "cree_par").all()


class PonderationHypothesesView(APIView):
    """GET /api/itineraires/ponderation/ — expose formules et coefficients fictifs (H3)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_hypotheses_ponderation())


class PointsRoutiersLectureView(generics.ListAPIView):
    """GET /api/itineraires/points/ — liste en lecture seule des points routiers."""

    permission_classes = [IsAuthenticated]
    serializer_class = PointRoutierSimpleSerializer
    queryset = PointRoutier.objects.all()
