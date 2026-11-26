"""Routes API REST du module itinéraires (Yannis)."""

from django.urls import path
from apps.itineraires.views import (
    CalculHistoriqueDetailView,
    CalculHistoriqueListView,
    CalculerItineraireView,
    ComparerItinerairesView,
    PointsRoutiersLectureView,
    PonderationHypothesesView,
)

app_name = "itineraires"

urlpatterns = [
    path("calculer/", CalculerItineraireView.as_view(), name="calculer-itineraire"),
    path("comparer/", ComparerItinerairesView.as_view(), name="comparer-itineraires"),
    path("calculs/", CalculHistoriqueListView.as_view(), name="historique-calculs"),
    path("calculs/<int:pk>/", CalculHistoriqueDetailView.as_view(), name="detail-calcul"),
    path("ponderation/", PonderationHypothesesView.as_view(), name="ponderation-hypotheses"),
    path("points/", PointsRoutiersLectureView.as_view(), name="points-lecture"),
]
