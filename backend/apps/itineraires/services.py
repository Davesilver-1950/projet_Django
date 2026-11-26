"""Services applicatifs du moteur d'itinéraires (lecture directe DB sans cache, RG-06)."""

import time
from rest_framework.exceptions import ValidationError

from apps.itineraires.dijkstra import (
    NoeudInfo,
    ResultatItineraire,
    calculer_itineraire_ordonne,
    construire_graphe,
)
from apps.itineraires.models import CalculItineraire
from apps.itineraires.ponderation import CRITERES_VALIDES, get_hypotheses_ponderation
from apps.reseau.models import PointRoutier, TronconRoutier


def _charger_reseau_en_direct(points_ids: list[int]) -> tuple[dict[int, NoeudInfo], list[TronconRoutier]]:
    """Lit les points et tronçons directement en base (aucun cache, RG-06)."""
    points = list(PointRoutier.objects.all())
    noeuds_map = {
        p.id: NoeudInfo(id=p.id, nom=p.nom, quartier=p.quartier, repere=p.repere)
        for p in points
    }
    manquants = [pid for pid in points_ids if pid not in noeuds_map]
    if manquants:
        raise ValidationError(
            {"points_ids": [f"Point(s) routier(s) introuvable(s) : {manquants}."]}
        )

    troncons = list(TronconRoutier.objects.select_related("origine", "destination").all())
    return noeuds_map, troncons


def _serialiser_resultat(
    resultat: ResultatItineraire,
    duree_calcul_ms: float,
    calcul_id: int | None = None,
    libelle: str = "",
) -> dict:
    payload = resultat.to_dict()
    payload.update(
        {
            "calcul_id": calcul_id,
            "libelle": libelle,
            "duree_calcul_ms": round(duree_calcul_ms, 3),
            "donnees_fictives": True,
            "hypotheses": get_hypotheses_ponderation(),
        }
    )
    return payload


def calculer_et_sauvegarder_itineraire(
    points_ids: list[int],
    type_vehicule: str,
    critere: str,
    user=None,
    enregistrer: bool = True,
    libelle: str = "",
) -> dict:
    """Exécute Dijkstra sur l'état courant du réseau et persiste optionnellement CalculItineraire."""
    debut = time.perf_counter()
    noeuds_map, troncons = _charger_reseau_en_direct(points_ids)
    graphe = construire_graphe(troncons, type_vehicule)
    resultat = calculer_itineraire_ordonne(
        graphe=graphe,
        noeuds_map=noeuds_map,
        points_ids=points_ids,
        critere=critere,
        type_vehicule=type_vehicule,
    )
    duree_ms = (time.perf_counter() - debut) * 1000.0

    calcul_id = None
    if enregistrer:
        hypotheses = get_hypotheses_ponderation()
        calcul = CalculItineraire.objects.create(
            libelle=libelle,
            cree_par=user if getattr(user, "is_authenticated", False) else None,
            origine_id=points_ids[0],
            destination_id=points_ids[-1],
            points_demandes=list(points_ids),
            type_vehicule=type_vehicule,
            critere=critere,
            distance_totale_km=resultat.distance_totale_km,
            temps_total_min=resultat.temps_total_min,
            cout_total_fcfa=resultat.cout_total_fcfa,
            etapes_snapshot=[e.to_dict() for e in resultat.etapes],
            hypotheses_snapshot=hypotheses,
            donnees_fictives=True,
        )
        calcul_id = calcul.id

    return _serialiser_resultat(
        resultat=resultat,
        duree_calcul_ms=duree_ms,
        calcul_id=calcul_id,
        libelle=libelle,
    )


def comparer_trois_criteres(points_ids: list[int], type_vehicule: str) -> dict:
    """Compare distance, temps estimé et coût pondéré sur le réseau courant (EF-14)."""
    debut = time.perf_counter()
    noeuds_map, troncons = _charger_reseau_en_direct(points_ids)
    graphe = construire_graphe(troncons, type_vehicule)

    resultats: dict[str, ResultatItineraire] = {}
    for critere in CRITERES_VALIDES:
        resultats[critere] = calculer_itineraire_ordonne(
            graphe=graphe,
            noeuds_map=noeuds_map,
            points_ids=points_ids,
            critere=critere,
            type_vehicule=type_vehicule,
        )

    duree_ms = (time.perf_counter() - debut) * 1000.0
    ref = resultats["distance"]

    tableau_comparatif = []
    for critere in CRITERES_VALIDES:
        res = resultats[critere]
        tableau_comparatif.append(
            {
                "critere": critere,
                "distance_totale_km": res.distance_totale_km,
                "temps_total_min": res.temps_total_min,
                "cout_total_fcfa": res.cout_total_fcfa,
                "nombre_troncons": res.nombre_troncons,
                "noeuds_traverses_noms": res.noeuds_traverses_noms,
                "ecart_vs_distance_km": round(res.distance_totale_km - ref.distance_totale_km, 4),
                "ecart_vs_distance_temps_min": round(res.temps_total_min - ref.temps_total_min, 4),
                "ecart_vs_distance_cout_fcfa": round(res.cout_total_fcfa - ref.cout_total_fcfa, 4),
            }
        )

    res_temps = resultats["temps"]
    res_cout = resultats["cout"]
    if res_temps.noeuds_traverses_ids == ref.noeuds_traverses_ids:
        synthese = (
            f"Le trajet le plus court ({ref.distance_totale_km} km) est également "
            f"le plus rapide ({ref.temps_total_min} min)."
        )
    else:
        gain_temps = round(ref.temps_total_min - res_temps.temps_total_min, 2)
        surplus_km = round(res_temps.distance_totale_km - ref.distance_totale_km, 2)
        synthese = (
            f"Le critère 'temps' évite les zones congestionnées/dégradées : "
            f"il parcourt {surplus_km} km de plus mais économise {gain_temps} min "
            f"par rapport au chemin le plus court en distance. "
            f"Le critère 'coût' estime {res_cout.cout_total_fcfa} FCFA."
        )

    return {
        "mode": "trois_criteres",
        "type_vehicule": type_vehicule,
        "points_demandes_ids": list(points_ids),
        "tableau_comparatif": tableau_comparatif,
        "resultats_par_critere": {
            critere: res.to_dict() for critere, res in resultats.items()
        },
        "synthese": synthese,
        "duree_calcul_ms": round(duree_ms, 3),
        "donnees_fictives": True,
        "hypotheses": get_hypotheses_ponderation(),
    }


def _calcul_vers_dict(calcul: CalculItineraire) -> dict:
    noms = [calcul.origine.nom]
    for etape in calcul.etapes_snapshot:
        noms.append(etape.get("destination_nom", ""))
    return {
        "calcul_id": calcul.id,
        "libelle": calcul.libelle,
        "critere": calcul.critere,
        "type_vehicule": calcul.type_vehicule,
        "points_demandes_ids": calcul.points_demandes,
        "noeuds_traverses_noms": noms,
        "etapes": calcul.etapes_snapshot,
        "distance_totale_km": calcul.distance_totale_km,
        "temps_total_min": calcul.temps_total_min,
        "cout_total_fcfa": calcul.cout_total_fcfa,
        "nombre_troncons": len(calcul.etapes_snapshot),
        "cree_le": calcul.cree_le.isoformat() if calcul.cree_le else None,
        "donnees_fictives": calcul.donnees_fictives,
    }


def _pct(delta: float, base: float) -> float:
    if not base:
        return 0.0
    return round((delta / base) * 100.0, 2)


def comparer_avant_apres(
    calcul_avant: CalculItineraire,
    calcul_apres: CalculItineraire | None = None,
    recalculer: bool = False,
    user=None,
) -> dict:
    """Compare deux calculs (ou un calcul passé face au réseau actuel, EF-15)."""
    avant_data = _calcul_vers_dict(calcul_avant)

    if recalculer or calcul_apres is None:
        apres_data = calculer_et_sauvegarder_itineraire(
            points_ids=calcul_avant.points_demandes,
            type_vehicule=calcul_avant.type_vehicule,
            critere=calcul_avant.critere,
            user=user,
            enregistrer=True,
            libelle=f"{calcul_avant.libelle or f'Calcul #{calcul_avant.id}'} (recalcul)",
        )
    else:
        apres_data = _calcul_vers_dict(calcul_apres)

    delta_dist = round(apres_data["distance_totale_km"] - avant_data["distance_totale_km"], 4)
    delta_temps = round(apres_data["temps_total_min"] - avant_data["temps_total_min"], 4)
    delta_cout = round(apres_data["cout_total_fcfa"] - avant_data["cout_total_fcfa"], 4)

    ids_avant = [e["troncon_id"] for e in avant_data["etapes"]]
    ids_apres = [e["troncon_id"] for e in apres_data["etapes"]]
    set_avant = set(ids_avant)
    set_apres = set(ids_apres)

    troncons_evites_ids = [tid for tid in ids_avant if tid not in set_apres]
    troncons_ajoutes_ids = [tid for tid in ids_apres if tid not in set_avant]

    troncons_db = {
        t.id: t
        for t in TronconRoutier.objects.select_related("origine", "destination").filter(
            id__in=set_avant | set_apres
        )
    }

    troncons_evites = []
    for tid in troncons_evites_ids:
        t = troncons_db.get(tid)
        if t:
            raison = "modifié ou contourné"
            if t.est_ferme:
                raison = "tronçon fermé"
            elif t.etat_route == "impraticable":
                raison = "route impraticable"
            elif t.congestion == "forte":
                raison = "congestion forte"
            troncons_evites.append(
                {
                    "troncon_id": t.id,
                    "libelle": f"{t.origine.nom} -> {t.destination.nom}",
                    "est_ferme": t.est_ferme,
                    "etat_route": t.etat_route,
                    "congestion": t.congestion,
                    "raison": raison,
                }
            )

    troncons_ajoutes = []
    for tid in troncons_ajoutes_ids:
        t = troncons_db.get(tid)
        if t:
            troncons_ajoutes.append(
                {
                    "troncon_id": t.id,
                    "libelle": f"{t.origine.nom} -> {t.destination.nom}",
                    "distance_km": t.distance_km,
                    "congestion": t.congestion,
                    "etat_route": t.etat_route,
                }
            )

    if ids_avant == ids_apres and delta_dist == 0 and delta_temps == 0 and delta_cout == 0:
        explication = "Aucun changement d'itinéraire ni de métrique entre les deux calculs."
    elif troncons_evites:
        noms_evites = ", ".join(f"{x['libelle']} ({x['raison']})" for x in troncons_evites)
        explication = (
            f"Le nouveau parcours contourne : {noms_evites}. "
            f"Écart constaté : {delta_dist:+.2f} km ({_pct(delta_dist, avant_data['distance_totale_km']):+.1f}%), "
            f"{delta_temps:+.2f} min ({_pct(delta_temps, avant_data['temps_total_min']):+.1f}%), "
            f"{delta_cout:+.2f} FCFA."
        )
    else:
        explication = (
            f"Le parcours emprunte les mêmes tronçons mais l'état du réseau a modifié les métriques : "
            f"{delta_dist:+.2f} km, {delta_temps:+.2f} min, {delta_cout:+.2f} FCFA."
        )

    return {
        "mode": "avant_apres",
        "avant": avant_data,
        "apres": apres_data,
        "ecarts": {
            "distance_km": delta_dist,
            "distance_pct": _pct(delta_dist, avant_data["distance_totale_km"]),
            "temps_estime_min": delta_temps,
            "temps_pct": _pct(delta_temps, avant_data["temps_total_min"]),
            "cout_estime_fcfa": delta_cout,
            "cout_pct": _pct(delta_cout, avant_data["cout_total_fcfa"]),
        },
        "troncons_evites": troncons_evites,
        "troncons_ajoutes": troncons_ajoutes,
        "explication": explication,
        "donnees_fictives": True,
    }
