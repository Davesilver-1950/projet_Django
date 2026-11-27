# Moteur d'itinéraires SmartRoute CM (`apps.itineraires`)

> **Avertissement (ENF-09)** : toutes les formules, coefficients de congestion, coûts en FCFA et réseaux routiers manipulés par ce module sont **entièrement fictifs et simulés**.

## 1. Hypothèses et règles de gestion implémentées

- **H1 — Ordre de visite fixé par le gestionnaire** : `calculer_itineraire_ordonne` exécute Dijkstra entre chaque paire consécutive de points (`origine -> arrêt_1 -> ... -> destination`) et calcule les cumuls à chaque étape.
- **H2 — Orientation des tronçons** : chaque `TronconRoutier` est orienté (`origine -> destination`) ; `double_sens=True` crée l'arc inverse dans le graphe.
- **H3 & RG-05 — Pondération centralisée** : toutes les constantes sont regroupées dans `backend/apps/itineraires/ponderation.py`.
- **RG-01 — Exclusion des tronçons impraticables** : `est_troncon_praticable()` exclut `est_ferme=True`, `etat_route="impraticable"`, ou un tronçon non praticable pour le type de véhicule (`moto` vs `vehicule_leger`).
- **RG-02 & EF-13 — Aucun chemin** : lève `AucunItineraireError` -> réponse HTTP `422` (`{"code": "AUCUN_ITINERAIRE", ...}`).
- **RG-03 — Poids strictement positifs** : distance `<= 0` ou durée `<= 0` lève `PoidsInvalideError` -> HTTP `400` (`POIDS_INVALIDE`).
- **RG-06 — Aucun cache réseau** : chaque requête lit directement `PointRoutier` et `TronconRoutier` en base.

## 2. Formules et coefficients (`ponderation.py`)

$$
t = t_{\text{base}} \times k_{\text{congestion}} \times k_{\text{état}}
\qquad
c = d \times c_{\text{km}} + t \times c_{\text{min}} + d \times p_{\text{état}}
$$

| Paramètre | Moto | Véhicule léger |
| :--- | :---: | :---: |
| $k_{\text{congestion}}$ fluide | `1.0` | `1.0` |
| $k_{\text{congestion}}$ modérée | `1.25` | `1.5` |
| $k_{\text{congestion}}$ forte | `1.75` | `2.5` |
| $c_{\text{km}}$ (FCFA/km) | `60` | `180` |
| $c_{\text{min}}$ (FCFA/min) | `25` | `25` |

| État de route | $k_{\text{état}}$ | $p_{\text{état}}$ (FCFA/km) |
| :--- | :---: | :---: |
| `bon` | `1.0` | `0` |
| `degrade` | `1.3` | `20` |
| `tres_degrade` | `1.8` | `50` |
| `impraticable` | Exclu | Exclu |

**Exemple de contrôle (Section 5)** : pour $d = 2\text{ km}$, $t_{\text{base}} = 6\text{ min}$, congestion `forte`, route `degrade` :
- Moto : $t = 13.65\text{ min}$, $c = 501.25\text{ FCFA}$
- Véhicule léger : $t = 19.50\text{ min}$, $c = 887.50\text{ FCFA}$

## 3. Contrats API REST

### `POST /api/itineraires/calculer/` (Rôle : `gestionnaire`)

Requête :
```json
{
  "origine_id": 1,
  "etapes_ids": [5],
  "destination_id": 9,
  "type_vehicule": "vehicule_leger",
  "critere": "temps",
  "enregistrer": true,
  "libelle": "Livraison Bonamoussadi via Deido"
}
```

Réponse `200 OK` : retourne `calcul_id`, `distance_totale_km`, `temps_total_min`, `cout_total_fcfa`, `noeuds_traverses_noms`, `etapes` (avec cumuls par étape), `duree_calcul_ms` et `donnees_fictives: true`.

Erreur `422` si aucun chemin :
```json
{
  "code": "AUCUN_ITINERAIRE",
  "message": "Aucun itinéraire praticable trouvé entre 'Bonanjo' et 'Île Manoka' pour le type de véhicule 'moto'.",
  "details": {
    "origine_id": 1,
    "destination_id": 11,
    "origine": "Bonanjo",
    "destination": "Île Manoka",
    "type_vehicule": "moto"
  }
}
```

### `GET /api/itineraires/comparer/` (Rôle : `gestionnaire`)

- **Mode 3 critères** : `?origine_id=1&destination_id=9&type_vehicule=vehicule_leger`
- **Mode avant/après** : `?calcul_avant_id=1&recalculer=true` ou `?calcul_avant_id=1&calcul_apres_id=2`
- **Persistance** : en mode avant/après, un recalcul (`recalculer=true`, ou `calcul_apres_id` absent) enregistre un nouveau `CalculItineraire` dans l'historique, bien que la requête soit un `GET`.

### Autres endpoints du module

- `GET /api/itineraires/calculs/` et `GET /api/itineraires/calculs/{id}/` (`admin` ou `gestionnaire`)
- `GET /api/itineraires/ponderation/` (tout utilisateur authentifié)
- `GET /api/itineraires/points/` (tout utilisateur authentifié)

## 4. Tests automatisés (T1, T2 et scénarios associés)

Exécution : `python manage.py test apps.itineraires`

- **T1** (`test_t1_distance_minimale_petit_graphe`) : vérifie la distance minimale et les cumuls sur un petit graphe.
- **T2** (`test_t2_comparaison_distance_temps_cout_coherente` et `test_calculer_multi_arrets_et_comparer_trois_criteres`) : vérifie la cohérence des 3 critères.
- **Scénario de soutenance avant/après** (`test_scenario_soutenance_fermeture_troncon_et_comparaison_avant_apres`) : calcul initial, fermeture d'un tronçon emprunté, recalcul en direct et explication des écarts.
- **Performance (ENF-01)** : graphe de 100 points calculé en `< 1 s`.
