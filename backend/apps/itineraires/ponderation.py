"""Règles de pondération centralisées et fictives pour SmartRoute CM (RG-05, H3).

Toutes les constantes ci-dessous sont fictives (pédagogiques) et ne doivent pas
être présentées comme des mesures réelles de circulation à Douala.
"""

from dataclasses import dataclass
from apps.itineraires.exceptions import PoidsInvalideError

TYPES_VEHICULE_VALIDES = ("moto", "vehicule_leger")
CRITERES_VALIDES = ("distance", "temps", "cout")

# Coefficients de congestion selon le type de véhicule (Section 5)
K_CONGESTION: dict[str, dict[str, float]] = {
    "vehicule_leger": {
        "fluide": 1.0,
        "moderee": 1.5,
        "forte": 2.5,
    },
    "moto": {
        "fluide": 1.0,
        "moderee": 1.25,
        "forte": 1.75,
    },
}

# Coefficients liés à l'état de la route (Section 5)
K_ETAT: dict[str, float] = {
    "bon": 1.0,
    "degrade": 1.3,
    "tres_degrade": 1.8,
}

# Coûts fictifs en FCFA (Section 5)
COUT_KM_FCFA: dict[str, float] = {
    "moto": 60.0,
    "vehicule_leger": 180.0,
}

COUT_MIN_FCFA: float = 25.0

PENALITE_ETAT_KM_FCFA: dict[str, float] = {
    "bon": 0.0,
    "degrade": 20.0,
    "tres_degrade": 50.0,
}


@dataclass(frozen=True)
class MetriquesTroncon:
    """Poids calculés d'un tronçon pour les trois critères Dijkstra."""

    distance_km: float
    temps_estime_min: float
    cout_estime_fcfa: float


def valider_coefficients() -> None:
    """Vérifie la cohérence des coefficients centralisés (RG-03)."""
    for type_v in TYPES_VEHICULE_VALIDES:
        for niveau, val in K_CONGESTION[type_v].items():
            if val < 1.0:
                raise PoidsInvalideError(
                    f"K_CONGESTION[{type_v}][{niveau}]",
                    val,
                    "Les coefficients de congestion doivent être >= 1.0.",
                )
        if COUT_KM_FCFA[type_v] <= 0:
            raise PoidsInvalideError(
                f"COUT_KM_FCFA[{type_v}]",
                COUT_KM_FCFA[type_v],
                "Le coût kilométrique doit être strictement positif.",
            )

    for etat, val in K_ETAT.items():
        if val < 1.0:
            raise PoidsInvalideError(
                f"K_ETAT[{etat}]",
                val,
                "Les coefficients d'état de route doivent être >= 1.0.",
            )

    if COUT_MIN_FCFA < 0:
        raise PoidsInvalideError("COUT_MIN_FCFA", COUT_MIN_FCFA)

    for etat, pen in PENALITE_ETAT_KM_FCFA.items():
        if pen < 0:
            raise PoidsInvalideError(f"PENALITE_ETAT_KM_FCFA[{etat}]", pen)


def est_troncon_praticable(
    est_ferme: bool,
    etat_route: str,
    praticable_moto: bool,
    praticable_vehicule_leger: bool,
    type_vehicule: str,
) -> bool:
    """Détermine si un tronçon est utilisable par un type de véhicule (RG-01)."""
    if type_vehicule not in TYPES_VEHICULE_VALIDES:
        raise PoidsInvalideError(
            "type_vehicule",
            type_vehicule,
            f"Type de véhicule inconnu : '{type_vehicule}'.",
        )
    if est_ferme or etat_route == "impraticable":
        return False
    if type_vehicule == "moto":
        return bool(praticable_moto)
    return bool(praticable_vehicule_leger)


def calculer_metriques_troncon(
    distance_km: float,
    duree_base_min: float,
    congestion: str,
    etat_route: str,
    type_vehicule: str,
) -> MetriquesTroncon:
    """Calcule (distance, temps estimé, coût pondéré) pour un tronçon praticable.

    Formules (Section 5) :
      t = t_base * k_congestion * k_etat
      c = d * c_km + t * c_min + d * p_etat
    """
    valider_coefficients()

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
    if type_vehicule not in TYPES_VEHICULE_VALIDES:
        raise PoidsInvalideError("type_vehicule", type_vehicule)
    if congestion not in K_CONGESTION[type_vehicule]:
        raise PoidsInvalideError(
            "congestion",
            congestion,
            f"Niveau de congestion inconnu : '{congestion}'.",
        )
    if etat_route not in K_ETAT:
        raise PoidsInvalideError(
            "etat_route",
            etat_route,
            f"État de route non calculable : '{etat_route}'.",
        )

    k_cong = K_CONGESTION[type_vehicule][congestion]
    k_etat = K_ETAT[etat_route]
    temps_estime = round(float(duree_base_min) * k_cong * k_etat, 4)

    c_km = COUT_KM_FCFA[type_vehicule]
    p_etat = PENALITE_ETAT_KM_FCFA[etat_route]
    cout_estime = round(
        float(distance_km) * c_km + temps_estime * COUT_MIN_FCFA + float(distance_km) * p_etat,
        4,
    )

    return MetriquesTroncon(
        distance_km=round(float(distance_km), 4),
        temps_estime_min=temps_estime,
        cout_estime_fcfa=cout_estime,
    )


def get_hypotheses_ponderation() -> dict:
    """Retourne la documentation structurée des formules et coefficients actifs."""
    return {
        "donnees_fictives": True,
        "avertissement": (
            "Coefficients et formules purement fictifs destinés à la simulation "
            "pédagogique SmartRoute CM."
        ),
        "formules": {
            "temps_estime_min": "t = t_base * k_congestion * k_etat",
            "cout_estime_fcfa": "c = d * c_km + t * c_min + d * p_etat",
        },
        "coefficients": {
            "k_congestion": K_CONGESTION,
            "k_etat": K_ETAT,
            "cout_km_fcfa": COUT_KM_FCFA,
            "cout_min_fcfa": COUT_MIN_FCFA,
            "penalite_etat_km_fcfa": PENALITE_ETAT_KM_FCFA,
        },
    }
