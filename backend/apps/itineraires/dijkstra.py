"""Moteur de calcul d'itinéraire minimal (algorithme de Dijkstra) — SmartRoute CM."""

from dataclasses import asdict, dataclass
import heapq
from typing import Iterable

from apps.itineraires.exceptions import AucunItineraireError, PoidsInvalideError
from apps.itineraires.ponderation import (
    CRITERES_VALIDES,
    TYPES_VEHICULE_VALIDES,
    calculer_metriques_troncon,
    est_troncon_praticable,
)


@dataclass(frozen=True)
class NoeudInfo:
    """Informations descriptives d'un point routier du graphe."""

    id: int
    nom: str
    quartier: str = ""
    repere: str = ""


@dataclass(frozen=True)
class AreteGraphe:
    """Arc orienté prêt pour l'algorithme de Dijkstra."""

    troncon_id: int
    origine_id: int
    destination_id: int
    distance_km: float
    temps_estime_min: float
    cout_estime_fcfa: float
    congestion: str
    etat_route: str
    sens_inverse: bool = False

    def poids(self, critere: str) -> float:
        if critere == "distance":
            return self.distance_km
        if critere == "temps":
            return self.temps_estime_min
        if critere == "cout":
            return self.cout_estime_fcfa
        raise PoidsInvalideError("critere", critere, f"Critère inconnu : '{critere}'.")


@dataclass(frozen=True)
class EtapeCalculee:
    """Étape d'un itinéraire avec valeurs individuelles et cumulées (EF-16)."""

    rang: int
    troncon_id: int
    origine_id: int
    origine_nom: str
    origine_quartier: str
    origine_repere: str
    destination_id: int
    destination_nom: str
    destination_quartier: str
    destination_repere: str
    distance_km: float
    temps_estime_min: float
    cout_estime_fcfa: float
    distance_cumulee_km: float
    temps_cumule_min: float
    cout_cumule_fcfa: float
    congestion: str
    etat_route: str
    sens_inverse: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResultatItineraire:
    """Résultat complet d'un calcul de chemin pour un critère donné."""

    critere: str
    type_vehicule: str
    points_demandes_ids: list[int]
    noeuds_traverses_ids: list[int]
    noeuds_traverses_noms: list[str]
    etapes: list[EtapeCalculee]
    distance_totale_km: float
    temps_total_min: float
    cout_total_fcfa: float
    nombre_troncons: int

    def to_dict(self) -> dict:
        return {
            "critere": self.critere,
            "type_vehicule": self.type_vehicule,
            "points_demandes_ids": self.points_demandes_ids,
            "noeuds_traverses_ids": self.noeuds_traverses_ids,
            "noeuds_traverses_noms": self.noeuds_traverses_noms,
            "etapes": [etape.to_dict() for etape in self.etapes],
            "distance_totale_km": self.distance_totale_km,
            "temps_total_min": self.temps_total_min,
            "cout_total_fcfa": self.cout_total_fcfa,
            "nombre_troncons": self.nombre_troncons,
        }


def _extraire_champ(objet, champ: str, defaut=None):
    if isinstance(objet, dict):
        return objet.get(champ, defaut)
    return getattr(objet, champ, defaut)


def construire_graphe(
    troncons: Iterable,
    type_vehicule: str,
) -> dict[int, list[AreteGraphe]]:
    """Construit la liste d'adjacence orientée filtrée pour le véhicule (RG-01, H2)."""
    if type_vehicule not in TYPES_VEHICULE_VALIDES:
        raise PoidsInvalideError("type_vehicule", type_vehicule)

    graphe: dict[int, list[AreteGraphe]] = {}

    for troncon in troncons:
        troncon_id = _extraire_champ(troncon, "id")
        origine_id = _extraire_champ(troncon, "origine_id")
        destination_id = _extraire_champ(troncon, "destination_id")
        distance_km = _extraire_champ(troncon, "distance_km")
        duree_base_min = _extraire_champ(troncon, "duree_base_min")
        congestion = _extraire_champ(troncon, "congestion", "fluide")
        etat_route = _extraire_champ(troncon, "etat_route", "bon")
        praticable_moto = _extraire_champ(troncon, "praticable_moto", True)
        praticable_vl = _extraire_champ(troncon, "praticable_vehicule_leger", True)
        double_sens = _extraire_champ(troncon, "double_sens", True)
        est_ferme = _extraire_champ(troncon, "est_ferme", False)

        # RG-03 : tout tronçon avec distance ou durée <= 0 est refusé explicitement
        if distance_km is None or distance_km <= 0:
            raise PoidsInvalideError(
                "distance_km",
                distance_km,
                "La distance d'un tronçon doit être strictement positive (> 0).",
            )
        if duree_base_min is None or duree_base_min <= 0:
            raise PoidsInvalideError(
                "duree_base_min",
                duree_base_min,
                "La durée de base d'un tronçon doit être strictement positive (> 0).",
            )

        if not est_troncon_praticable(
            est_ferme=est_ferme,
            etat_route=etat_route,
            praticable_moto=praticable_moto,
            praticable_vehicule_leger=praticable_vl,
            type_vehicule=type_vehicule,
        ):
            continue

        metriques = calculer_metriques_troncon(
            distance_km=distance_km,
            duree_base_min=duree_base_min,
            congestion=congestion,
            etat_route=etat_route,
            type_vehicule=type_vehicule,
        )

        arete_directe = AreteGraphe(
            troncon_id=troncon_id,
            origine_id=origine_id,
            destination_id=destination_id,
            distance_km=metriques.distance_km,
            temps_estime_min=metriques.temps_estime_min,
            cout_estime_fcfa=metriques.cout_estime_fcfa,
            congestion=congestion,
            etat_route=etat_route,
            sens_inverse=False,
        )
        graphe.setdefault(origine_id, []).append(arete_directe)

        if double_sens:
            arete_inverse = AreteGraphe(
                troncon_id=troncon_id,
                origine_id=destination_id,
                destination_id=origine_id,
                distance_km=metriques.distance_km,
                temps_estime_min=metriques.temps_estime_min,
                cout_estime_fcfa=metriques.cout_estime_fcfa,
                congestion=congestion,
                etat_route=etat_route,
                sens_inverse=True,
            )
            graphe.setdefault(destination_id, []).append(arete_inverse)

    # Tri déterministe des arêtes sortantes
    for noeud_id in graphe:
        graphe[noeud_id].sort(key=lambda a: (a.destination_id, a.troncon_id))

    return graphe


def dijkstra(
    graphe: dict[int, list[AreteGraphe]],
    origine_id: int,
    destination_id: int,
    critere: str = "distance",
    noeuds_map: dict[int, NoeudInfo] | None = None,
    type_vehicule: str = "vehicule_leger",
) -> list[AreteGraphe]:
    """Calcule la suite d'arêtes de poids minimal entre origine_id et destination_id."""
    if critere not in CRITERES_VALIDES:
        raise PoidsInvalideError("critere", critere, f"Critère invalide : '{critere}'.")

    if origine_id == destination_id:
        return []

    distances: dict[int, float] = {origine_id: 0.0}
    precedents: dict[int, AreteGraphe] = {}
    file_priorite: list[tuple[float, int]] = [(0.0, origine_id)]
    visites: set[int] = set()

    while file_priorite:
        cout_courant, noeud_courant = heapq.heappop(file_priorite)
        if noeud_courant in visites:
            continue
        visites.add(noeud_courant)

        if noeud_courant == destination_id:
            break

        for arete in graphe.get(noeud_courant, ()):
            poids_arete = arete.poids(critere)
            if poids_arete <= 0:
                raise PoidsInvalideError(critere, poids_arete)

            voisin = arete.destination_id
            if voisin in visites:
                continue

            nouveau_cout = cout_courant + poids_arete
            if nouveau_cout < distances.get(voisin, float("inf")):
                distances[voisin] = nouveau_cout
                precedents[voisin] = arete
                heapq.heappush(file_priorite, (nouveau_cout, voisin))

    if destination_id not in precedents:
        origine_label = (
            noeuds_map[origine_id].nom
            if noeuds_map and origine_id in noeuds_map
            else str(origine_id)
        )
        dest_label = (
            noeuds_map[destination_id].nom
            if noeuds_map and destination_id in noeuds_map
            else str(destination_id)
        )
        raise AucunItineraireError(
            origine=origine_label,
            destination=dest_label,
            type_vehicule=type_vehicule,
            origine_id=origine_id,
            destination_id=destination_id,
        )

    chemin: list[AreteGraphe] = []
    curseur = destination_id
    while curseur != origine_id:
        arete = precedents[curseur]
        chemin.append(arete)
        curseur = arete.origine_id
    chemin.reverse()
    return chemin


def calculer_itineraire_ordonne(
    graphe: dict[int, list[AreteGraphe]],
    noeuds_map: dict[int, NoeudInfo],
    points_ids: list[int],
    critere: str = "distance",
    type_vehicule: str = "vehicule_leger",
) -> ResultatItineraire:
    """Calcule un itinéraire passant par une liste ordonnée de points (H1)."""
    if len(points_ids) < 2:
        raise ValueError("Au moins deux points (départ et arrivée) sont requis.")
    if critere not in CRITERES_VALIDES:
        raise PoidsInvalideError("critere", critere, f"Critère invalide : '{critere}'.")
    if type_vehicule not in TYPES_VEHICULE_VALIDES:
        raise PoidsInvalideError("type_vehicule", type_vehicule)

    aretes_totales: list[AreteGraphe] = []
    for index in range(len(points_ids) - 1):
        depart_segment = points_ids[index]
        arrivee_segment = points_ids[index + 1]
        segment_aretes = dijkstra(
            graphe=graphe,
            origine_id=depart_segment,
            destination_id=arrivee_segment,
            critere=critere,
            noeuds_map=noeuds_map,
            type_vehicule=type_vehicule,
        )
        aretes_totales.extend(segment_aretes)

    etapes: list[EtapeCalculee] = []
    cumul_dist = 0.0
    cumul_temps = 0.0
    cumul_cout = 0.0

    noeuds_traverses_ids = [points_ids[0]]

    for rang, arete in enumerate(aretes_totales, start=1):
        cumul_dist = round(cumul_dist + arete.distance_km, 4)
        cumul_temps = round(cumul_temps + arete.temps_estime_min, 4)
        cumul_cout = round(cumul_cout + arete.cout_estime_fcfa, 4)

        orig = noeuds_map.get(
            arete.origine_id, NoeudInfo(id=arete.origine_id, nom=f"Point {arete.origine_id}")
        )
        dest = noeuds_map.get(
            arete.destination_id,
            NoeudInfo(id=arete.destination_id, nom=f"Point {arete.destination_id}"),
        )

        etapes.append(
            EtapeCalculee(
                rang=rang,
                troncon_id=arete.troncon_id,
                origine_id=arete.origine_id,
                origine_nom=orig.nom,
                origine_quartier=orig.quartier,
                origine_repere=orig.repere,
                destination_id=arete.destination_id,
                destination_nom=dest.nom,
                destination_quartier=dest.quartier,
                destination_repere=dest.repere,
                distance_km=arete.distance_km,
                temps_estime_min=arete.temps_estime_min,
                cout_estime_fcfa=arete.cout_estime_fcfa,
                distance_cumulee_km=cumul_dist,
                temps_cumule_min=cumul_temps,
                cout_cumule_fcfa=cumul_cout,
                congestion=arete.congestion,
                etat_route=arete.etat_route,
                sens_inverse=arete.sens_inverse,
            )
        )
        noeuds_traverses_ids.append(arete.destination_id)

    noeuds_traverses_noms = [
        noeuds_map[nid].nom if nid in noeuds_map else f"Point {nid}"
        for nid in noeuds_traverses_ids
    ]

    return ResultatItineraire(
        critere=critere,
        type_vehicule=type_vehicule,
        points_demandes_ids=list(points_ids),
        noeuds_traverses_ids=noeuds_traverses_ids,
        noeuds_traverses_noms=noeuds_traverses_noms,
        etapes=etapes,
        distance_totale_km=cumul_dist,
        temps_total_min=cumul_temps,
        cout_total_fcfa=cumul_cout,
        nombre_troncons=len(etapes),
    )
