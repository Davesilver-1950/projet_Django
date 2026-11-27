# SmartRoute CM — Aide à la planification des tournées de livraison

> **Avertissement (données fictives)** : Toutes les données de ce projet (points routiers inspirés de Douala, temps de trajet, niveaux de congestion, coûts en FCFA, immatriculations, numéros de téléphone et comptes utilisateurs) sont **entièrement fictives et simulées** à des fins pédagogiques. Elles ne doivent jamais être présentées comme des mesures réelles de la circulation au Cameroun.

## 1. Présentation

**SmartRoute CM** (Projet 4 — CDWFS Projets Django) est une application web d'aide à la planification des tournées de livraison urbaine adaptée au contexte d'un réseau routier simplifié : routes dégradées, tronçons fermés, congestion différenciée selon le type de véhicule (`moto` vs `véhicule léger`).

### Architecture imposée (3 couches)

```text
Vue.js 3 + Vite (navigateur)  <── HTTP/JSON (JWT) ──>  API Django REST Framework  <── ORM ──>  PostgreSQL (ou repli SQLite)
```

- Aucun accès direct à la base de données depuis le navigateur.
- Toutes les règles métier, permissions par rôle (`Administrateur`, `Gestionnaire`, `Livreur`) et calculs Dijkstra sont exécutés côté serveur.

### Découpage en 5 modules (équipe)

| Membre | Branche | Module Django (`backend/apps/`) | Responsabilités principales |
| :--- | :--- | :--- | :--- |
| **Yannis** (Lead Tech) | `feat/yannis-dijkstra` | `itineraires` | Architecture dépôt, `/api/health/`, `ponderation.py`, Dijkstra multi-critères, comparaisons, tests T1/T2 |
| **Sandra** | `feat/sandra-auth` | `accounts` | Authentification JWT, gestion comptes/rôles, sécurité, test T3 |
| **Serena** | `feat/serena-reseau` | `reseau` | Points & tronçons routiers, contraintes, fermeture/réouverture, fixtures 3 scénarios, tests T4/T5/T6 |
| **Daphné** | `feat/daphne-flotte` | `flotte` | Véhicules, livreurs, points de livraison, colis, contrôle capacité, test T7 |
| **Larue** | `feat/larue-tournees` | `tournees` | Tournées, étapes ordonnées, vue livreur mobile, test T8 |

---

## 2. Prérequis

- **Python** `3.12+` (testé avec Python 3.14)
- **Node.js** `20+` et **npm**
- **PostgreSQL** `15+` (recommandé en production/soutenance) — ou SQLite intégré pour le développement local rapide (`DB_ENGINE=sqlite`).
- **Git**

---

## 3. Installation et lancement (nouveau poste en moins de 30 min)

### 3.1 Cloner et configurer l'environnement

```bash
git clone https://github.com/Davesilver-1950/projet_Django.git
cd projet_Django
cp .env.example .env
```

Adaptez `.env` avec vos identifiants PostgreSQL (`DB_ENGINE=postgresql` par défaut dans `.env.example`).

#### Initialisation de la base PostgreSQL

Créez la base et l'utilisateur dans PostgreSQL (`psql -U postgres`) :

```sql
CREATE USER smartroute_user WITH PASSWORD 'mot_de_passe_fictif_local';
CREATE DATABASE smartroute_cm OWNER smartroute_user;
```

*(Optionnel)* Pour un test rapide sans PostgreSQL local, passez `DB_ENGINE=sqlite` dans `.env`.

### 3.2 Back-end Django

```bash
cd backend
python -m venv .venv
```

Activer l'environnement virtuel :
- **Windows (PowerShell)** : `.\.venv\Scripts\Activate.ps1`
- **Linux / macOS** : `source .venv/bin/activate`

Installer les dépendances, appliquer les migrations, charger le jeu de démonstration fictif et lancer le serveur :

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_itineraires
python manage.py runserver
```

Comptes fictifs créés par `seed_demo_itineraires` (usage local uniquement) :
- **Gestionnaire** : `gestionnaire_demo` / `SmartRouteGest2026!`
- **Administrateur** : `admin_demo` / `SmartRouteAdmin2026!`
- **Livreur** : `livreur_demo` / `SmartRouteLiv2026!`

Vérification rapide : ouvrir `http://127.0.0.1:8000/api/health/` — doit renvoyer HTTP `200` avec `"status": "ok"` et `"donnees_fictives": true`.

### 3.3 Front-end Vue.js + Vite

Dans un second terminal, depuis la racine du dépôt :

```bash
cd frontend
npm install
npm run dev
```

L'interface est accessible sur `http://localhost:5173`.

---

## 4. Tests automatisés

Depuis le dossier `backend/` (avec l'environnement virtuel activé) :

```bash
python manage.py test
```

Tests du module `itineraires` (T1, T2, pondération, permissions API, erreur `422 AUCUN_ITINERAIRE`, scénario avant/après, performance 100 nœuds) :

```bash
python manage.py test apps.itineraires
```

Documentation technique du moteur d'itinéraires : [`docs/moteur-itineraires.md`](docs/moteur-itineraires.md).

---

## 5. Workflow Git de l'équipe

- `main` : branche protégée des jalons validés (`v0.1`, `v0.2`, `v1.0`).
- `dev` : branche d'intégration commune.
- `feat/<prenom>-<module>` : branches de fonctionnalités fusionnées dans `dev` via Pull Request relue.
- **Sécurité** : aucun secret (`.env`, mots de passe réels) ni base locale (`db.sqlite3`) ne doit être versionné.
