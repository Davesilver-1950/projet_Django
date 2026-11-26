"""Sérialiseurs DRF pour le moteur d'itinéraires."""

from rest_framework import serializers

from apps.flotte.models import TypeVehicule
from apps.itineraires.models import CalculItineraire
from apps.reseau.models import PointRoutier
from apps.tournees.models import CritereOptimisation


def resoudre_points_ordonnes(
    origine_id: int | None = None,
    destination_id: int | None = None,
    etapes_ids: list[int] | None = None,
    points_ids: list[int] | None = None,
) -> list[int]:
    """Construit la liste ordonnée des identifiants de points à traverser (H1)."""
    if points_ids:
        if len(points_ids) < 2:
            raise serializers.ValidationError(
                {"points_ids": "Au moins deux points (départ et arrivée) sont requis."}
            )
        return points_ids

    if origine_id is None or destination_id is None:
        raise serializers.ValidationError(
            "Fournissez soit 'points_ids', soit 'origine_id' et 'destination_id'."
        )

    intermediaires = etapes_ids or []
    return [origine_id, *intermediaires, destination_id]


class CalculItineraireRequeteSerializer(serializers.Serializer):
    """Validation de la requête POST /api/itineraires/calculer/."""

    origine_id = serializers.IntegerField(required=False, min_value=1)
    destination_id = serializers.IntegerField(required=False, min_value=1)
    etapes_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
    )
    points_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
    )
    type_vehicule = serializers.ChoiceField(
        choices=TypeVehicule.choices,
        default=TypeVehicule.VEHICULE_LEGER,
    )
    critere = serializers.ChoiceField(
        choices=CritereOptimisation.choices,
        default=CritereOptimisation.DISTANCE,
    )
    enregistrer = serializers.BooleanField(required=False, default=True)
    libelle = serializers.CharField(required=False, allow_blank=True, max_length=160, default="")

    def validate(self, attrs):
        points_ordonnes = resoudre_points_ordonnes(
            origine_id=attrs.get("origine_id"),
            destination_id=attrs.get("destination_id"),
            etapes_ids=attrs.get("etapes_ids"),
            points_ids=attrs.get("points_ids"),
        )
        attrs["points_ordonnes"] = points_ordonnes
        return attrs


class CalculItineraireHistoriqueSerializer(serializers.ModelSerializer):
    """Sérialiseur de lecture pour l'historique des calculs enregistrés."""

    origine_nom = serializers.CharField(source="origine.nom", read_only=True)
    destination_nom = serializers.CharField(source="destination.nom", read_only=True)
    cree_par_username = serializers.CharField(
        source="cree_par.username", read_only=True, default=None
    )

    class Meta:
        model = CalculItineraire
        fields = [
            "id",
            "libelle",
            "cree_par_username",
            "origine",
            "origine_nom",
            "destination",
            "destination_nom",
            "points_demandes",
            "type_vehicule",
            "critere",
            "distance_totale_km",
            "temps_total_min",
            "cout_total_fcfa",
            "etapes_snapshot",
            "hypotheses_snapshot",
            "donnees_fictives",
            "cree_le",
        ]
        read_only_fields = fields


class PointRoutierSimpleSerializer(serializers.ModelSerializer):
    """Sérialiseur minimal des points routiers pour alimenter l'écran itinéraires."""

    class Meta:
        model = PointRoutier
        fields = ["id", "nom", "quartier", "repere", "x", "y"]
        read_only_fields = fields
