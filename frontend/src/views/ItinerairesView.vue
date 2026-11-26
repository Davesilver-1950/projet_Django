<template>
  <section class="itineraires-page">
    <div class="alert-warning fictif-notice" role="note">
      <strong>Simulation :</strong> résultats calculés sur des données fictives (graphe et coûts pédagogiques SmartRoute CM).
    </div>

    <div v-if="role && role !== 'gestionnaire'" class="alert-warning" role="status">
      Connecté avec le rôle <strong>{{ role }}</strong>. Le calcul et la comparaison d'itinéraires sont réservés au rôle <strong>Gestionnaire logistique</strong> (403 sinon).
    </div>

    <div class="card">
      <div class="title-row">
        <h1>Planification et comparaison d'itinéraires (Dijkstra)</h1>
        <button type="button" class="btn btn-secondary btn-sm" @click="showPonderation = !showPonderation">
          {{ showPonderation ? "Masquer les hypothèses" : "Hypothèses temps / coût" }}
        </button>
      </div>

      <div v-if="showPonderation && ponderation" class="ponderation-panel">
        <h4>Formules et coefficients actifs (fictifs — <code>ponderation.py</code>)</h4>
        <p>
          <code>{{ ponderation.formules.temps_estime_min }}</code><br />
          <code>{{ ponderation.formules.cout_estime_fcfa }}</code>
        </p>
        <div class="coef-grid">
          <div>
            <strong>k_congestion (VL) :</strong>
            Fluide {{ ponderation.coefficients.k_congestion.vehicule_leger.fluide }} ·
            Modérée {{ ponderation.coefficients.k_congestion.vehicule_leger.moderee }} ·
            Forte {{ ponderation.coefficients.k_congestion.vehicule_leger.forte }}
          </div>
          <div>
            <strong>k_congestion (Moto) :</strong>
            Fluide {{ ponderation.coefficients.k_congestion.moto.fluide }} ·
            Modérée {{ ponderation.coefficients.k_congestion.moto.moderee }} ·
            Forte {{ ponderation.coefficients.k_congestion.moto.forte }}
          </div>
          <div>
            <strong>k_état :</strong>
            Bon {{ ponderation.coefficients.k_etat.bon }} ·
            Dégradé {{ ponderation.coefficients.k_etat.degrade }} ·
            Très dégradé {{ ponderation.coefficients.k_etat.tres_degrade }}
          </div>
          <div>
            <strong>Coûts :</strong>
            Moto {{ ponderation.coefficients.cout_km_fcfa.moto }} FCFA/km ·
            VL {{ ponderation.coefficients.cout_km_fcfa.vehicule_leger }} FCFA/km ·
            Temps {{ ponderation.coefficients.cout_min_fcfa }} FCFA/min
          </div>
        </div>
      </div>

      <div v-if="erreur" class="alert-error" role="alert">
        <strong>{{ erreur.code }}</strong> — {{ erreur.message }}
        <div v-if="erreur.details" class="error-details">
          {{ JSON.stringify(erreur.details) }}
        </div>
      </div>

      <form @submit.prevent="lancerCalcul">
        <div class="form-grid">
          <div class="form-group">
            <label for="origine">Point de départ</label>
            <select id="origine" v-model="origineId" class="select" required>
              <option disabled value="">Choisir un point...</option>
              <option v-for="p in points" :key="p.id" :value="p.id">
                {{ p.nom }} ({{ p.quartier }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="destination">Point d'arrivée</label>
            <select id="destination" v-model="destinationId" class="select" required>
              <option disabled value="">Choisir un point...</option>
              <option v-for="p in points" :key="p.id" :value="p.id">
                {{ p.nom }} ({{ p.quartier }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="vehicule">Type de véhicule</label>
            <select id="vehicule" v-model="typeVehicule" class="select">
              <option value="vehicule_leger">Véhicule léger</option>
              <option value="moto">Moto</option>
            </select>
          </div>

          <div class="form-group">
            <label for="critere">Critère principal</label>
            <select id="critere" v-model="critere" class="select">
              <option value="distance">Distance minimale (km)</option>
              <option value="temps">Temps estimé minimal (min)</option>
              <option value="cout">Coût pondéré minimal (FCFA)</option>
            </select>
          </div>
        </div>

        <div class="stops-section">
          <div class="stops-header">
            <label>Arrêts intermédiaires ordonnés (optionnel, H1)</label>
            <button type="button" class="btn btn-secondary btn-sm" @click="ajouterArret">
              + Ajouter un arrêt
            </button>
          </div>

          <div v-for="(stopId, idx) in etapesIds" :key="idx" class="stop-row">
            <span class="badge">Arrêt {{ idx + 1 }}</span>
            <select v-model="etapesIds[idx]" class="select" required>
              <option disabled value="">Choisir un point intermédiaire...</option>
              <option v-for="p in points" :key="p.id" :value="p.id">
                {{ p.nom }} ({{ p.quartier }})
              </option>
            </select>
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="idx === 0"
              @click="deplacerArret(idx, -1)"
              title="Monter"
            >
              ↑
            </button>
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="idx === etapesIds.length - 1"
              @click="deplacerArret(idx, 1)"
              title="Descendre"
            >
              ↓
            </button>
            <button type="button" class="btn btn-danger btn-sm" @click="retirerArret(idx)">
              Retirer
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="libelle">Libellé du calcul (pour comparaison avant/après)</label>
          <input
            id="libelle"
            v-model.trim="libelle"
            type="text"
            class="input"
            placeholder="Ex. : Livraison Bonamoussadi — scénario normal"
          />
        </div>

        <div class="actions-row">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? "Calcul en cours..." : "Calculer l'itinéraire" }}
          </button>
          <button type="button" class="btn btn-secondary" :disabled="loading" @click="lancerComparaison3">
            Comparer les 3 critères
          </button>
        </div>
      </form>
    </div>

    <TableauComparatif
      v-if="comparaison3"
      :tableau="comparaison3.tableau_comparatif"
      :synthese="comparaison3.synthese"
      :critere-selectionne="critereCompareActif"
      @select-critere="critereCompareActif = $event"
    />

    <ListeEtapes
      v-if="resultatAffiche"
      :resultat="resultatAffiche"
      :titre="titreResultatAffiche"
    />

    <ComparaisonAvantApres
      :calculs="historique"
      @refresh-historique="chargerHistorique"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import ComparaisonAvantApres from "../components/itineraires/ComparaisonAvantApres.vue";
import ListeEtapes from "../components/itineraires/ListeEtapes.vue";
import TableauComparatif from "../components/itineraires/TableauComparatif.vue";
import { extractApiError } from "../services/api";
import {
  calculerItineraire,
  comparerCriteres,
  getCalculs,
  getPoints,
  getPonderation,
} from "../services/itinerairesService";
import { useAuth } from "../stores/auth";

const { role } = useAuth();

const points = ref([]);
const ponderation = ref(null);
const historique = ref([]);
const showPonderation = ref(false);

const origineId = ref("");
const destinationId = ref("");
const etapesIds = ref([]);
const typeVehicule = ref("vehicule_leger");
const critere = ref("distance");
const libelle = ref("");

const loading = ref(false);
const erreur = ref(null);
const resultatSimple = ref(null);
const comparaison3 = ref(null);
const critereCompareActif = ref("distance");

const resultatAffiche = computed(() => {
  if (comparaison3.value) {
    return comparaison3.value.resultats_par_critere[critereCompareActif.value] || null;
  }
  return resultatSimple.value;
});

const titreResultatAffiche = computed(() => {
  if (comparaison3.value) {
    return `Étapes du critère « ${critereCompareActif.value} »`;
  }
  return "Liste ordonnée des étapes";
});

onMounted(async () => {
  try {
    const [pts, pond] = await Promise.all([getPoints(), getPonderation()]);
    points.value = pts;
    ponderation.value = pond;
    if (pts.length >= 2) {
      origineId.value = pts[0].id;
      destinationId.value = pts[pts.length - 1].id;
    }
    await chargerHistorique();
  } catch (err) {
    erreur.value = extractApiError(err);
  }
});

async function chargerHistorique() {
  if (role.value === "admin" || role.value === "gestionnaire") {
    try {
      historique.value = await getCalculs();
    } catch {
      historique.value = [];
    }
  }
}

function ajouterArret() {
  etapesIds.value.push("");
}

function retirerArret(idx) {
  etapesIds.value.splice(idx, 1);
}

function deplacerArret(idx, direction) {
  const cible = idx + direction;
  if (cible < 0 || cible >= etapesIds.value.length) return;
  const copie = [...etapesIds.value];
  [copie[idx], copie[cible]] = [copie[cible], copie[idx]];
  etapesIds.value = copie;
}

function validerSelection() {
  if (!origineId.value || !destinationId.value) {
    erreur.value = {
      code: "DONNEES_INVALIDES",
      message: "Veuillez sélectionner un point de départ et un point d'arrivée.",
    };
    return false;
  }
  return true;
}

async function lancerCalcul() {
  if (!validerSelection()) return;
  loading.value = true;
  erreur.value = null;
  comparaison3.value = null;
  try {
    const cleanEtapes = etapesIds.value.filter(Boolean).map(Number);
    resultatSimple.value = await calculerItineraire({
      origine_id: Number(origineId.value),
      destination_id: Number(destinationId.value),
      etapes_ids: cleanEtapes,
      type_vehicule: typeVehicule.value,
      critere: critere.value,
      enregistrer: true,
      libelle: libelle.value,
    });
    await chargerHistorique();
  } catch (err) {
    erreur.value = extractApiError(err);
  } finally {
    loading.value = false;
  }
}

async function lancerComparaison3() {
  if (!validerSelection()) return;
  loading.value = true;
  erreur.value = null;
  resultatSimple.value = null;
  try {
    const cleanEtapes = etapesIds.value.filter(Boolean).map(Number);
    comparaison3.value = await comparerCriteres({
      origine_id: Number(origineId.value),
      destination_id: Number(destinationId.value),
      etapes_ids: cleanEtapes,
      type_vehicule: typeVehicule.value,
    });
    critereCompareActif.value = "distance";
  } catch (err) {
    erreur.value = extractApiError(err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.itineraires-page {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.title-row h1 {
  margin: 0;
  font-size: 1.35rem;
}

.ponderation-panel {
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.9rem 1rem;
  margin-bottom: 1rem;
}

.ponderation-panel h4 {
  margin-top: 0;
}

.coef-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.5rem;
  font-size: 0.88rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.85rem;
}

.stops-section {
  margin-bottom: 0.9rem;
}

.stops-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.stops-header label {
  font-size: 0.88rem;
  font-weight: 600;
}

.stop-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.5rem;
}

.stop-row .select {
  flex: 1 1 200px;
}

.actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.error-details {
  font-size: 0.82rem;
  margin-top: 0.25rem;
}
</style>
