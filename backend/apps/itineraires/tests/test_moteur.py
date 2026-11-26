"""Tests unitaires du moteur Dijkstra et de ponderation.py (T1, T2, RG-01..05, ENF-01)."""

import time
from django.test import SimpleTestCase

from apps.itineraires.dijkstra import (
    NoeudInfo,
    calculer_itineraire_ordonne,
    construire_graphe,
    dijkstra,
)
from apps.itineraires.exceptions import AucunItineraireError, PoidsInvalideError
from apps.itineraires.ponderation import calculer_metriques_troncon


class PonderationTests(SimpleTestCase):
    """Vérifie les formules de pondération (Section 5) et le contrôle des poids."""

    def test_exemple_controle_section_5(self):
        """2 km, 6 min de base, forte congestion, route dégradée -> valeurs exactes."""
        moto = calculer_metriques_troncon(
            distance_km=2.0,
            duree_base_min=6.0,
            congestion="forte",
            etat_route="degrade",
            type_vehicule="moto",
        )
        self.assertEqual(moto.temps_estime_min, 13.65)
        self.assertEqual(moto.cout_estime_fcfa, 501.25)

        voiture = calculer_metriques_troncon(
            distance_km=2.0,
            duree_base_min=6.0,
            congestion="forte",
            etat_route="degrade",
            type_vehicule="vehicule_leger",
        )
        self.assertEqual(voiture.temps_estime_min, 19.5)
        self.assertEqual(voiture.cout_estime_fcfa, 887.5)

    def test_poids_negatif_ou_nul_refuse(self):
        """RG-03 : distance <= 0 ou durée <= 0 refusée."""
        with self.assertRaises(PoidsInvalideError) as ctx_dist:
            calculer_metriques_troncon(0, 5.0, "fluide", "bon", "moto")
        self.assertEqual(ctx_dist.exception.champ, "distance_km")

        with self.assertRaises(PoidsInvalideError) as ctx_dur:
            calculer_metriques_troncon(2.0, -3.0, "fluide", "bon", "vehicule_leger")
        self.assertEqual(ctx_dur.exception.champ, "duree_base_min")


class DijkstraMoteurTests(SimpleTestCase):
    """Tests unitaires du graphe routier et de Dijkstra (T1, T2 et règles métier)."""

    def setUp(self):
        self.noeuds = {
            1: NoeudInfo(1, "Bonanjo", "Bonanjo", "Rond-point 4e"),
            2: NoeudInfo(2, "Akwa", "Akwa", "Carrefour Soudanaise"),
            3: NoeudInfo(3, "Deido", "Deido", "Rond-point Deido"),
            4: NoeudInfo(4, "Makepe", "Makepe", "Carrefour Lycée"),
            5: NoeudInfo(5, "Bonamoussadi", "Bonamoussadi", "Entrée Sable"),
        }

    def test_t1_distance_minimale_petit_graphe(self):
        """T1 : Dijkstra retrouve le chemin minimal attendu en distance sur petit graphe."""
        troncons = [
            {
                "id": 10,
                "origine_id": 1,
                "destination_id": 2,
                "distance_km": 2.0,
                "duree_base_min": 5.0,
                "congestion": "fluide",
                "etat_route": "bon",
                "double_sens": True,
            },
            {
                "id": 11,
                "origine_id": 2,
                "destination_id": 5,
                "distance_km": 3.0,
                "duree_base_min": 8.0,
                "congestion": "fluide",
                "etat_route": "bon",
                "double_sens": True,
            },
            {
                "id": 12,
                "origine_id": 1,
                "destination_id": 3,
                "distance_km": 4.0,
                "duree_base_min": 6.0,
                "congestion": "fluide",
                "etat_route": "bon",
                "double_sens": True,
            },
            {
                "id": 13,
                "origine_id": 3,
                "destination_id": 5,
                "distance_km": 4.5,
                "duree_base_min": 7.0,
                "congestion": "fluide",
                "etat_route": "bon",
                "double_sens": True,
            },
        ]

        graphe = construire_graphe(troncons, "vehicule_leger")
        res = calculer_itineraire_ordonne(
            graphe, self.noeuds, [1, 5], critere="distance", type_vehicule="vehicule_leger"
        )

        self.assertEqual(res.noeuds_traverses_ids, [1, 2, 5])
        self.assertEqual(res.distance_totale_km, 5.0)
        self.assertEqual(res.nombre_troncons, 2)
        self.assertEqual(res.etapes[0].distance_cumulee_km, 2.0)
        self.assertEqual(res.etapes[1].distance_cumulee_km, 5.0)

    def test_t2_comparaison_distance_temps_cout_coherente(self):
        """T2 : Chemin court mais très congestionné vs détour plus long mais fluide."""
        troncons = [
            # Route directe courte mais congestion forte et dégradée (1 -> 2 -> 5 = 4 km)
            {
                "id": 20,
                "origine_id": 1,
                "destination_id": 2,
                "distance_km": 2.0,
                "duree_base_min": 8.0,
                "congestion": "forte",
                "etat_route": "tres_degrade",
                "double_sens": True,
            },
            {
                "id": 21,
                "origine_id": 2,
                "destination_id": 5,
                "distance_km": 2.0,
                "duree_base_min": 8.0,
                "congestion": "forte",
                "etat_route": "tres_degrade",
                "double_sens": True,
            },
            # Détour plus long en km (7 km) mais fluide et bon état
            {
                "id": 22,
                "origine_id": 1,
                "destination_id": 3,
                "distance_km": 3.5,
                "duree_base_min": 4.0,
                "congestion": "fluide",
                "etat_route": "bon",
                "double_sens": True,
            },
            {
                "id": 23,
                "origine_id": 3,
                "destination_id": 5,
                "distance_km": 3.5,
                "duree_base_min": 4.0,
                "congestion": "fluide",
                "etat_route": "bon",
                "double_sens": True,
            },
        ]

        graphe = construire_graphe(troncons, "vehicule_leger")
        res_dist = calculer_itineraire_ordonne(graphe, self.noeuds, [1, 5], "distance", "vehicule_leger")
        res_temps = calculer_itineraire_ordonne(graphe, self.noeuds, [1, 5], "temps", "vehicule_leger")
        res_cout = calculer_itineraire_ordonne(graphe, self.noeuds, [1, 5], "cout", "vehicule_leger")

        self.assertEqual(res_dist.noeuds_traverses_ids, [1, 2, 5])
        self.assertEqual(res_temps.noeuds_traverses_ids, [1, 3, 5])
        self.assertLessEqual(res_dist.distance_totale_km, res_temps.distance_totale_km)
        self.assertLessEqual(res_temps.temps_total_min, res_dist.temps_total_min)
        self.assertLessEqual(res_cout.cout_total_fcfa, res_dist.cout_total_fcfa)
        self.assertLessEqual(res_cout.cout_total_fcfa, res_temps.cout_total_fcfa)

    def test_troncons_fermes_et_impraticables_exclus(self):
        """RG-01 : tronçons fermés ou impraticables pour le véhicule sont exclus."""
        troncons = [
            {
                "id": 30,
                "origine_id": 1,
                "destination_id": 5,
                "distance_km": 1.0,
                "duree_base_min": 2.0,
                "est_ferme": True,
            },
            {
                "id": 31,
                "origine_id": 1,
                "destination_id": 4,
                "distance_km": 3.0,
                "duree_base_min": 5.0,
                "praticable_vehicule_leger": False,
                "praticable_moto": True,
            },
            {
                "id": 32,
                "origine_id": 4,
                "destination_id": 5,
                "distance_km": 2.0,
                "duree_base_min": 4.0,
                "praticable_vehicule_leger": True,
                "praticable_moto": True,
            },
        ]

        # La moto peut passer par 1 -> 4 -> 5
        graphe_moto = construire_graphe(troncons, "moto")
        res_moto = calculer_itineraire_ordonne(graphe_moto, self.noeuds, [1, 5], "distance", "moto")
        self.assertEqual(res_moto.noeuds_traverses_ids, [1, 4, 5])

        # Le véhicule léger n'a aucun chemin (30 fermé, 31 impraticable en voiture)
        graphe_vl = construire_graphe(troncons, "vehicule_leger")
        with self.assertRaises(AucunItineraireError):
            dijkstra(graphe_vl, 1, 5, "distance", self.noeuds, "vehicule_leger")

    def test_sens_unique_et_tournee_ordonnee(self):
        """H1 & H2 : respect du sens unique et des arrêts intermédiaires ordonnés."""
        troncons = [
            {
                "id": 40,
                "origine_id": 1,
                "destination_id": 2,
                "distance_km": 2.0,
                "duree_base_min": 4.0,
                "double_sens": False,
            },
            {
                "id": 41,
                "origine_id": 2,
                "destination_id": 3,
                "distance_km": 2.5,
                "duree_base_min": 5.0,
                "double_sens": True,
            },
        ]
        graphe = construire_graphe(troncons, "moto")
        res = calculer_itineraire_ordonne(graphe, self.noeuds, [1, 2, 3], "distance", "moto")
        self.assertEqual(res.noeuds_traverses_ids, [1, 2, 3])
        self.assertEqual(res.distance_totale_km, 4.5)

        # Le retour 2 -> 1 est interdit car 40 est à sens unique
        with self.assertRaises(AucunItineraireError):
            dijkstra(graphe, 2, 1, "distance", self.noeuds, "moto")

    def test_poids_negatif_dans_graphe_refuse(self):
        """RG-03 : construire_graphe refuse un tronçon avec distance ou durée <= 0."""
        troncons = [
            {
                "id": 50,
                "origine_id": 1,
                "destination_id": 2,
                "distance_km": -1.5,
                "duree_base_min": 4.0,
            }
        ]
        with self.assertRaises(PoidsInvalideError):
            construire_graphe(troncons, "moto")

    def test_performance_100_noeuds_sous_1_seconde(self):
        """ENF-01 : calcul sur un graphe de 100 points en moins de 1 seconde."""
        noeuds_100 = {i: NoeudInfo(i, f"Point {i}", "Douala") for i in range(1, 101)}
        troncons = []
        tid = 1
        for i in range(1, 100):
            troncons.append(
                {
                    "id": tid,
                    "origine_id": i,
                    "destination_id": i + 1,
                    "distance_km": 1.2,
                    "duree_base_min": 2.5,
                    "double_sens": True,
                }
            )
            tid += 1
            if i + 5 <= 100:
                troncons.append(
                    {
                        "id": tid,
                        "origine_id": i,
                        "destination_id": i + 5,
                        "distance_km": 4.8,
                        "duree_base_min": 7.0,
                        "congestion": "moderee",
                        "double_sens": True,
                    }
                )
                tid += 1

        debut = time.perf_counter()
        graphe = construire_graphe(troncons, "vehicule_leger")
        res = calculer_itineraire_ordonne(
            graphe, noeuds_100, [1, 50, 100], "cout", "vehicule_leger"
        )
        duree = time.perf_counter() - debut

        self.assertLess(duree, 1.0)
        self.assertGreater(res.nombre_troncons, 0)
