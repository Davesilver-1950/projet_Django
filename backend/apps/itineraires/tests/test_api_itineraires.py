"""Tests d'intégration API REST du module itinéraires (permissions, T2, 422, avant/après)."""

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import RoleUtilisateur, Utilisateur
from apps.reseau.models import EtatRoute, NiveauCongestion, PointRoutier, TronconRoutier


class ItinerairesAPITests(APITestCase):
    """Vérifie les endpoints /api/itineraires/calculer/, /comparer/, /calculs/, /ponderation/."""

    def setUp(self):
        self.admin = Utilisateur.objects.create_user(
            username="admin_test",
            email="admin@test.cm",
            password="PasswordTest123!",
            role=RoleUtilisateur.ADMIN,
        )
        self.gestionnaire = Utilisateur.objects.create_user(
            username="gest_test",
            email="gest@test.cm",
            password="PasswordTest123!",
            role=RoleUtilisateur.GESTIONNAIRE,
        )
        self.livreur = Utilisateur.objects.create_user(
            username="liv_test",
            email="liv@test.cm",
            password="PasswordTest123!",
            role=RoleUtilisateur.LIVREUR,
        )

        # Graphe fictif Douala simplifié
        self.p_bonanjo = PointRoutier.objects.create(
            nom="Bonanjo", quartier="Bonanjo", repere="Place du Gouvernement"
        )
        self.p_akwa = PointRoutier.objects.create(
            nom="Akwa", quartier="Akwa", repere="Carrefour Soudanaise"
        )
        self.p_deido = PointRoutier.objects.create(
            nom="Deido", quartier="Deido", repere="Rond-point Deido"
        )
        self.p_bonamoussadi = PointRoutier.objects.create(
            nom="Bonamoussadi", quartier="Bonamoussadi", repere="Entrée Sable"
        )
        self.p_makepe = PointRoutier.objects.create(
            nom="Makepe", quartier="Makepe", repere="Carrefour Lycée"
        )
        self.p_isole = PointRoutier.objects.create(
            nom="Île Manoka", quartier="Manoka", repere="Débarcadère"
        )

        # Route directe courte mais très congestionnée : Bonanjo -> Akwa -> Bonamoussadi (5 km)
        self.t_bonanjo_akwa = TronconRoutier.objects.create(
            origine=self.p_bonanjo,
            destination=self.p_akwa,
            distance_km=2.0,
            duree_base_min=8.0,
            congestion=NiveauCongestion.FORTE,
            etat_route=EtatRoute.DEGRADE,
            double_sens=True,
        )
        self.t_akwa_bonamoussadi = TronconRoutier.objects.create(
            origine=self.p_akwa,
            destination=self.p_bonamoussadi,
            distance_km=3.0,
            duree_base_min=10.0,
            congestion=NiveauCongestion.FORTE,
            etat_route=EtatRoute.TRES_DEGRADE,
            double_sens=True,
        )

        # Détour plus long mais fluide : Bonanjo -> Deido -> Makepe -> Bonamoussadi (8 km)
        self.t_bonanjo_deido = TronconRoutier.objects.create(
            origine=self.p_bonanjo,
            destination=self.p_deido,
            distance_km=3.0,
            duree_base_min=4.0,
            congestion=NiveauCongestion.FLUIDE,
            etat_route=EtatRoute.BON,
            double_sens=True,
        )
        self.t_deido_makepe = TronconRoutier.objects.create(
            origine=self.p_deido,
            destination=self.p_makepe,
            distance_km=3.0,
            duree_base_min=4.0,
            congestion=NiveauCongestion.FLUIDE,
            etat_route=EtatRoute.BON,
            double_sens=True,
        )
        self.t_makepe_bonamoussadi = TronconRoutier.objects.create(
            origine=self.p_makepe,
            destination=self.p_bonamoussadi,
            distance_km=2.0,
            duree_base_min=3.0,
            congestion=NiveauCongestion.FLUIDE,
            etat_route=EtatRoute.BON,
            double_sens=True,
        )

        self.url_calculer = reverse("itineraires:calculer-itineraire")
        self.url_comparer = reverse("itineraires:comparer-itineraires")

    def test_permissions_401_et_403(self):
        """Anonyme -> 401 ; Livreur & Admin -> 403 ; Gestionnaire -> 200."""
        payload = {
            "origine_id": self.p_bonanjo.id,
            "destination_id": self.p_bonamoussadi.id,
            "type_vehicule": "vehicule_leger",
            "critere": "distance",
        }

        # Sans authentification
        res_anon = self.client.post(self.url_calculer, payload, format="json")
        self.assertEqual(res_anon.status_code, 401)
        self.assertEqual(res_anon.json()["code"], "NON_AUTHENTIFIE")

        # Livreur refusé
        self.client.force_authenticate(user=self.livreur)
        res_liv = self.client.post(self.url_calculer, payload, format="json")
        self.assertEqual(res_liv.status_code, 403)
        self.assertEqual(res_liv.json()["code"], "ACCES_INTERDIT")

        # Administrateur refusé pour le calcul et la comparaison
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.post(self.url_calculer, payload, format="json")
        self.assertEqual(res_admin.status_code, 403)

        res_admin_cmp = self.client.get(
            self.url_comparer,
            {
                "origine_id": self.p_bonanjo.id,
                "destination_id": self.p_bonamoussadi.id,
                "type_vehicule": "moto",
            },
        )
        self.assertEqual(res_admin_cmp.status_code, 403)

        # Gestionnaire autorisé
        self.client.force_authenticate(user=self.gestionnaire)
        res_gest = self.client.post(self.url_calculer, payload, format="json")
        self.assertEqual(res_gest.status_code, 200)
        self.assertTrue(res_gest.json()["donnees_fictives"])

    def test_calculer_multi_arrets_et_comparer_trois_criteres(self):
        """T2 via API + calcul multi-arrêts ordonnés."""
        self.client.force_authenticate(user=self.gestionnaire)

        # Calcul multi-arrêts : Bonanjo -> Deido -> Bonamoussadi
        res_multi = self.client.post(
            self.url_calculer,
            {
                "origine_id": self.p_bonanjo.id,
                "etapes_ids": [self.p_deido.id],
                "destination_id": self.p_bonamoussadi.id,
                "type_vehicule": "moto",
                "critere": "temps",
                "libelle": "Tournée via Deido",
            },
            format="json",
        )
        self.assertEqual(res_multi.status_code, 200)
        data_multi = res_multi.json()
        self.assertIsNotNone(data_multi["calcul_id"])
        self.assertIn("Deido", data_multi["noeuds_traverses_noms"])
        self.assertEqual(data_multi["distance_totale_km"], 8.0)

        # Comparaison des 3 critères Bonanjo -> Bonamoussadi
        res_cmp = self.client.get(
            self.url_comparer,
            {
                "origine_id": self.p_bonanjo.id,
                "destination_id": self.p_bonamoussadi.id,
                "type_vehicule": "vehicule_leger",
            },
        )
        self.assertEqual(res_cmp.status_code, 200)
        cmp_data = res_cmp.json()
        self.assertEqual(cmp_data["mode"], "trois_criteres")
        self.assertEqual(len(cmp_data["tableau_comparatif"]), 3)

        dist_res = cmp_data["resultats_par_critere"]["distance"]
        temps_res = cmp_data["resultats_par_critere"]["temps"]
        self.assertEqual(dist_res["noeuds_traverses_noms"], ["Bonanjo", "Akwa", "Bonamoussadi"])
        self.assertEqual(
            temps_res["noeuds_traverses_noms"],
            ["Bonanjo", "Deido", "Makepe", "Bonamoussadi"],
        )
        self.assertLessEqual(dist_res["distance_totale_km"], temps_res["distance_totale_km"])
        self.assertLessEqual(temps_res["temps_total_min"], dist_res["temps_total_min"])

    def test_scenario_soutenance_fermeture_troncon_et_comparaison_avant_apres(self):
        """EF-15 & RG-06 : fermeture d'un tronçon emprunté -> nouveau parcours et écarts expliqués."""
        self.client.force_authenticate(user=self.gestionnaire)

        # 1. Calcul initial en distance -> passe par Bonanjo -> Akwa -> Bonamoussadi (5 km)
        res_avant = self.client.post(
            self.url_calculer,
            {
                "origine_id": self.p_bonanjo.id,
                "destination_id": self.p_bonamoussadi.id,
                "type_vehicule": "vehicule_leger",
                "critere": "distance",
                "libelle": "Avant fermeture Akwa",
            },
            format="json",
        )
        self.assertEqual(res_avant.status_code, 200)
        calcul_avant_id = res_avant.json()["calcul_id"]

        # 2. Fermeture du tronçon Akwa -> Bonamoussadi
        self.t_akwa_bonamoussadi.est_ferme = True
        self.t_akwa_bonamoussadi.save()

        # 3. Comparaison avant/après avec recalcul en direct (aucun cache)
        res_cmp = self.client.get(
            self.url_comparer,
            {"calcul_avant_id": calcul_avant_id, "recalculer": "true"},
        )
        self.assertEqual(res_cmp.status_code, 200)
        data = res_cmp.json()
        self.assertEqual(data["mode"], "avant_apres")
        self.assertEqual(
            data["apres"]["noeuds_traverses_noms"],
            ["Bonanjo", "Deido", "Makepe", "Bonamoussadi"],
        )
        self.assertEqual(data["ecarts"]["distance_km"], 3.0)
        self.assertEqual(len(data["troncons_evites"]), 2)
        evites_par_id = {item["troncon_id"]: item for item in data["troncons_evites"]}
        self.assertIn(self.t_akwa_bonamoussadi.id, evites_par_id)
        self.assertEqual(evites_par_id[self.t_akwa_bonamoussadi.id]["raison"], "tronçon fermé")
        self.assertIn("contourne", data["explication"])

    def test_absence_de_chemin_retourne_422_aucun_itineraire(self):
        """EF-13 & RG-02 : point isolé -> 422 AUCUN_ITINERAIRE avec détails."""
        self.client.force_authenticate(user=self.gestionnaire)
        res = self.client.post(
            self.url_calculer,
            {
                "origine_id": self.p_bonanjo.id,
                "destination_id": self.p_isole.id,
                "type_vehicule": "moto",
                "critere": "distance",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 422)
        body = res.json()
        self.assertEqual(body["code"], "AUCUN_ITINERAIRE")
        self.assertEqual(body["details"]["origine"], "Bonanjo")
        self.assertEqual(body["details"]["destination"], "Île Manoka")
        self.assertEqual(body["details"]["origine_id"], self.p_bonanjo.id)
        self.assertEqual(body["details"]["destination_id"], self.p_isole.id)

    def test_entrees_invalides_retournent_400_structure(self):
        """ENF-04 : critère inconnu, point inexistant -> 400 structuré, jamais 500."""
        self.client.force_authenticate(user=self.gestionnaire)

        res_bad_critere = self.client.post(
            self.url_calculer,
            {
                "origine_id": self.p_bonanjo.id,
                "destination_id": self.p_bonamoussadi.id,
                "critere": "inconnu",
            },
            format="json",
        )
        self.assertEqual(res_bad_critere.status_code, 400)
        self.assertEqual(res_bad_critere.json()["code"], "DONNEES_INVALIDES")

        res_bad_point = self.client.post(
            self.url_calculer,
            {
                "origine_id": self.p_bonanjo.id,
                "destination_id": 99999,
                "critere": "distance",
            },
            format="json",
        )
        self.assertEqual(res_bad_point.status_code, 400)
        self.assertEqual(res_bad_point.json()["code"], "DONNEES_INVALIDES")
