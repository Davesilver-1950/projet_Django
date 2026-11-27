"""Exceptions métier spécifiques au moteur d'itinéraires SmartRoute CM."""


class PoidsInvalideError(Exception):
    """Levée lorsqu'un poids de graphe (distance, durée, coefficient) est <= 0 ou invalide."""

    code = "POIDS_INVALIDE"

    def __init__(self, champ: str, valeur, message: str | None = None):
        self.champ = champ
        self.valeur = valeur
        self.message = message or (
            f"Le champ '{champ}' doit être strictement positif pour Dijkstra (reçu : {valeur})."
        )
        super().__init__(self.message)


class AucunItineraireError(Exception):
    """Levée lorsqu'aucun chemin praticable n'existe entre deux points (EF-13, RG-02)."""

    code = "AUCUN_ITINERAIRE"

    def __init__(
        self,
        origine,
        destination,
        type_vehicule: str,
        message: str | None = None,
        origine_id: int | None = None,
        destination_id: int | None = None,
    ):
        self.origine_id = origine_id
        self.destination_id = destination_id
        self.origine = origine
        self.destination = destination
        self.type_vehicule = type_vehicule
        self.message = message or (
            f"Aucun itinéraire praticable trouvé entre '{origine}' et '{destination}' "
            f"pour le type de véhicule '{type_vehicule}'."
        )
        super().__init__(self.message)
