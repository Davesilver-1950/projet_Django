"""Commande de démonstration fictive pour tester le moteur d'itinéraires."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import RoleUtilisateur, Utilisateur
from apps.flotte.models import Livreur, TypeVehicule, Vehicule
from apps.reseau.models import EtatRoute, NiveauCongestion, PointRoutier, TronconRoutier


class Command(BaseCommand):
    help = "Charge un jeu de données fictives (utilisateurs, graphe Douala 10 points / 16 tronçons)."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Comptes fictifs
        comptes = [
            ("admin_demo", "admin.demo@smartroute.test", RoleUtilisateur.ADMIN, "SmartRouteAdmin2026!"),
            ("gestionnaire_demo", "gestionnaire.demo@smartroute.test", RoleUtilisateur.GESTIONNAIRE, "SmartRouteGest2026!"),
            ("livreur_demo", "livreur.demo@smartroute.test", RoleUtilisateur.LIVREUR, "SmartRouteLiv2026!"),
        ]
        for username, email, role, password in comptes:
            user, created = Utilisateur.objects.get_or_create(
                username=username,
                defaults={"email": email, "role": role, "is_active": True},
            )
            if created:
                user.set_password(password)
                user.save()

        livreur_user = Utilisateur.objects.get(username="livreur_demo")
        Livreur.objects.get_or_create(
            utilisateur=livreur_user,
            defaults={
                "nom": "Jean-Paul Mbarga (Fictif)",
                "telephone_fictif": "600-00-00-01",
                "disponible": True,
            },
        )

        # 2. Véhicules fictifs
        Vehicule.objects.get_or_create(
            immatriculation_fictif="LT-001-DEMO",
            defaults={"type_vehicule": TypeVehicule.MOTO, "capacite_kg": 40.0},
        )
        Vehicule.objects.get_or_create(
            immatriculation_fictif="LT-002-DEMO",
            defaults={"type_vehicule": TypeVehicule.VEHICULE_LEGER, "capacite_kg": 350.0},
        )

        # 3. 10 points routiers fictifs inspirés de Douala
        points_data = [
            ("Bonanjo", "Bonanjo", "Place du Gouvernement", 10.0, 10.0),
            ("Akwa", "Akwa", "Carrefour Soudanaise", 25.0, 20.0),
            ("Bali", "Bali", "Rue Koumassi", 20.0, 8.0),
            ("Bonapriso", "Bonapriso", "Carrefour Armée de l'Air", 15.0, 3.0),
            ("Deido", "Deido", "Rond-point Deido", 35.0, 35.0),
            ("Bepanda", "Bepanda", "Carrefour Omnisports", 45.0, 28.0),
            ("Ndokotti", "Ndokotti", "Carrefour Ndokotti", 55.0, 22.0),
            ("Makepe", "Makepe", "Carrefour Lycée", 50.0, 48.0),
            ("Bonamoussadi", "Bonamoussadi", "Entrée Sable", 42.0, 60.0),
            ("Logbaba", "Logbaba", "Carrefour Total", 72.0, 25.0),
        ]
        points_map = {}
        for nom, quartier, repere, x, y in points_data:
            pt, _ = PointRoutier.objects.get_or_create(
                nom=nom,
                defaults={"quartier": quartier, "repere": repere, "x": x, "y": y},
            )
            points_map[nom] = pt

        # 4. 16 tronçons routiers fictifs
        troncons_data = [
            ("Bonanjo", "Akwa", 2.1, 6.0, NiveauCongestion.MODEREE, EtatRoute.BON, True, True, True, False),
            ("Bonanjo", "Bali", 1.8, 5.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, True, True, False),
            ("Bali", "Bonapriso", 1.6, 4.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, True, True, False),
            ("Bali", "Akwa", 2.0, 6.0, NiveauCongestion.FORTE, EtatRoute.DEGRADE, True, True, True, False),
            ("Akwa", "Deido", 2.4, 7.0, NiveauCongestion.FORTE, EtatRoute.DEGRADE, True, True, True, False),
            ("Bonapriso", "Ndokotti", 5.8, 12.0, NiveauCongestion.MODEREE, EtatRoute.BON, True, True, True, False),
            ("Akwa", "Bepanda", 3.2, 8.0, NiveauCongestion.MODEREE, EtatRoute.BON, True, True, True, False),
            ("Deido", "Bonamoussadi", 4.1, 9.0, NiveauCongestion.FORTE, EtatRoute.TRES_DEGRADE, True, True, True, False),
            ("Deido", "Makepe", 3.6, 8.0, NiveauCongestion.MODEREE, EtatRoute.DEGRADE, True, True, True, False),
            ("Bepanda", "Makepe", 3.0, 6.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, True, True, False),
            ("Bepanda", "Ndokotti", 2.2, 7.0, NiveauCongestion.FORTE, EtatRoute.DEGRADE, True, True, True, False),
            ("Makepe", "Bonamoussadi", 2.5, 5.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, True, True, False),
            ("Ndokotti", "Makepe", 4.0, 9.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, True, True, False),
            ("Ndokotti", "Logbaba", 3.5, 8.0, NiveauCongestion.MODEREE, EtatRoute.DEGRADE, True, True, True, False),
            ("Makepe", "Logbaba", 5.2, 11.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, False, True, False),
            ("Bonamoussadi", "Logbaba", 6.5, 14.0, NiveauCongestion.FLUIDE, EtatRoute.BON, True, True, False, False),
        ]

        for (
            orig_nom,
            dest_nom,
            dist,
            duree,
            cong,
            etat,
            p_moto,
            p_vl,
            double_sens,
            ferme,
        ) in troncons_data:
            TronconRoutier.objects.get_or_create(
                origine=points_map[orig_nom],
                destination=points_map[dest_nom],
                defaults={
                    "distance_km": dist,
                    "duree_base_min": duree,
                    "congestion": cong,
                    "etat_route": etat,
                    "praticable_moto": p_moto,
                    "praticable_vehicule_leger": p_vl,
                    "double_sens": double_sens,
                    "est_ferme": ferme,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Jeu de données fictives chargé : 3 comptes, 10 points routiers, 16 tronçons."
            )
        )
