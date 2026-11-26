import api from "./api";

export async function getPoints() {
  const res = await api.get("/itineraires/points/");
  return res.data;
}

export async function getPonderation() {
  const res = await api.get("/itineraires/ponderation/");
  return res.data;
}

export async function getCalculs() {
  const res = await api.get("/itineraires/calculs/");
  return res.data;
}

export async function calculerItineraire(payload) {
  const res = await api.post("/itineraires/calculer/", payload);
  return res.data;
}

export async function comparerCriteres({
  origine_id,
  destination_id,
  etapes_ids = [],
  type_vehicule = "vehicule_leger",
}) {
  const params = new URLSearchParams({
    origine_id: String(origine_id),
    destination_id: String(destination_id),
    type_vehicule,
  });
  if (etapes_ids.length > 0) {
    params.set("etapes_ids", etapes_ids.join(","));
  }
  const res = await api.get(`/itineraires/comparer/?${params.toString()}`);
  return res.data;
}

export async function comparerAvantApres({
  calcul_avant_id,
  calcul_apres_id = null,
  recalculer = false,
}) {
  const params = new URLSearchParams({
    calcul_avant_id: String(calcul_avant_id),
    recalculer: recalculer ? "true" : "false",
  });
  if (calcul_apres_id) {
    params.set("calcul_apres_id", String(calcul_apres_id));
  }
  const res = await api.get(`/itineraires/comparer/?${params.toString()}`);
  return res.data;
}
