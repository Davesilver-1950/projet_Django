"""Tests du module Authentification, rôles et sécurité (Sandra)."""

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import RoleUtilisateur, Utilisateur
from apps.flotte.models import Livreur

MOT_DE_PASSE = "MotDePasseFictif123"


def creer_compte(username, role):
    return Utilisateur.objects.create_user(
        username=username,
        email=f"{username}@exemple.fictif",
        password=MOT_DE_PASSE,
        role=role,
    )


class AuthentificationTests(APITestCase):
    def setUp(self):
        self.livreur = creer_compte("livreur1", RoleUtilisateur.LIVREUR)

    def test_connexion_valide_renvoie_jetons_et_role(self):
        r = self.client.post(
            reverse("accounts:token-obtain-pair"),
            {"username": "livreur1", "password": MOT_DE_PASSE},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)
        self.assertEqual(r.data["user"]["role"], "livreur")
        self.assertNotIn("password", r.data["user"])

    def test_mauvais_mot_de_passe_refuse_401(self):
        r = self.client.post(
            reverse("accounts:token-obtain-pair"),
            {"username": "livreur1", "password": "faux"},
        )
        self.assertEqual(r.status_code, 401)

    def test_compte_inactif_refuse_401(self):
        self.livreur.is_active = False
        self.livreur.save()
        r = self.client.post(
            reverse("accounts:token-obtain-pair"),
            {"username": "livreur1", "password": MOT_DE_PASSE},
        )
        self.assertEqual(r.status_code, 401)

    def test_profil_sans_jeton_refuse_401(self):
        r = self.client.get(reverse("accounts:profil-courant"))
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["code"], "NON_AUTHENTIFIE")


class PermissionsComptesTests(APITestCase):
    def setUp(self):
        self.admin = creer_compte("admin1", RoleUtilisateur.ADMIN)
        self.gestionnaire = creer_compte("gestionnaire1", RoleUtilisateur.GESTIONNAIRE)
        self.livreur = creer_compte("livreur1", RoleUtilisateur.LIVREUR)
        self.url = reverse("accounts:utilisateur-list")

    def test_sans_jeton_401(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_livreur_interdit_403(self):
        self.client.force_authenticate(self.livreur)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["code"], "ACCES_INTERDIT")

    def test_gestionnaire_interdit_403(self):
        self.client.force_authenticate(self.gestionnaire)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_autorise_et_mot_de_passe_jamais_renvoye(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("password", r.json()[0] if isinstance(r.json(), list) else r.json()["results"][0])

    def test_livreur_ne_peut_pas_creer_un_compte_403(self):
        self.client.force_authenticate(self.livreur)
        r = self.client.post(
            self.url,
            {"username": "pirate", "email": "p@x.fictif", "password": MOT_DE_PASSE, "role": "admin"},
        )
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Utilisateur.objects.filter(username="pirate").exists())


class CrudComptesTests(APITestCase):
    def setUp(self):
        self.admin = creer_compte("admin1", RoleUtilisateur.ADMIN)
        self.client.force_authenticate(self.admin)
        self.url = reverse("accounts:utilisateur-list")

    def test_creation_livreur_cree_le_profil_et_hache_le_mot_de_passe(self):
        r = self.client.post(
            self.url,
            {
                "username": "nouveau",
                "email": "nouveau@exemple.fictif",
                "password": MOT_DE_PASSE,
                "role": "livreur",
                "nom": "Livreur Fictif",
                "telephone_fictif": "670000000",
            },
        )
        self.assertEqual(r.status_code, 201)
        compte = Utilisateur.objects.get(username="nouveau")
        self.assertNotEqual(compte.password, MOT_DE_PASSE)
        self.assertTrue(compte.check_password(MOT_DE_PASSE))
        self.assertEqual(Livreur.objects.get(utilisateur=compte).nom, "Livreur Fictif")

    def test_mot_de_passe_obligatoire_a_la_creation_400(self):
        r = self.client.post(
            self.url, {"username": "sans_mdp", "email": "s@x.fictif", "role": "gestionnaire"}
        )
        self.assertEqual(r.status_code, 400)

    def test_mot_de_passe_trop_court_400(self):
        r = self.client.post(
            self.url,
            {"username": "court", "email": "c@x.fictif", "password": "abc", "role": "livreur"},
        )
        self.assertEqual(r.status_code, 400)

    def test_email_unique_400(self):
        creer_compte("existant", RoleUtilisateur.LIVREUR)
        r = self.client.post(
            self.url,
            {
                "username": "autre",
                "email": "existant@exemple.fictif",
                "password": MOT_DE_PASSE,
                "role": "livreur",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_admin_ne_peut_pas_se_retirer_son_role_403(self):
        url = reverse("accounts:utilisateur-detail", args=[self.admin.pk])
        r = self.client.patch(url, {"role": "livreur"})
        self.assertEqual(r.status_code, 403)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, RoleUtilisateur.ADMIN)

    def test_admin_ne_peut_pas_se_supprimer_403(self):
        url = reverse("accounts:utilisateur-detail", args=[self.admin.pk])
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_creation_gestionnaire_sans_profil_livreur_201(self):
        r = self.client.post(
            self.url,
            {
                "username": "gest",
                "email": "gest@exemple.fictif",
                "password": MOT_DE_PASSE,
                "role": "gestionnaire",
            },
        )
        self.assertEqual(r.status_code, 201)
        self.assertFalse(Livreur.objects.filter(utilisateur__username="gest").exists())

    def test_passage_au_role_livreur_cree_un_seul_profil(self):
        compte = creer_compte("futur", RoleUtilisateur.GESTIONNAIRE)
        url = reverse("accounts:utilisateur-detail", args=[compte.pk])
        r = self.client.patch(url, {"role": "livreur", "nom": "Livreur Fictif"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.patch(url, {"first_name": "Test"}).status_code, 200)
        self.assertEqual(Livreur.objects.get(utilisateur=compte).nom, "Livreur Fictif")

    def test_suppression_dun_autre_compte_204(self):
        autre = creer_compte("autre", RoleUtilisateur.GESTIONNAIRE)
        url = reverse("accounts:utilisateur-detail", args=[autre.pk])
        self.assertEqual(self.client.delete(url).status_code, 204)