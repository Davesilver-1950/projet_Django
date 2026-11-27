"""Tests du socle SmartRoute CM."""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    """Vérifie l'accessibilité et le format JSON de GET /api/health/."""

    def test_health_check_retourne_200_et_donnees_fictives(self):
        client = APIClient()
        url = reverse("health-check")
        response = client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "SmartRoute CM API")
        self.assertEqual(data["database"], "ok")
        self.assertTrue(data["donnees_fictives"])


class RouteApiInconnueTests(TestCase):
    """ENF-04 : une URL inconnue sous /api/ renvoie un 404 JSON uniforme."""

    def test_url_inconnue_retourne_404_json(self):
        client = APIClient()
        for response in (client.get("/api/inconnu/"), client.post("/api/reseau/inconnu/")):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["code"], "RESSOURCE_INTROUVABLE")

    def test_redirection_slash_final_conservee(self):
        response = APIClient().get("/api/health")
        self.assertRedirects(response, "/api/health/", status_code=301)
