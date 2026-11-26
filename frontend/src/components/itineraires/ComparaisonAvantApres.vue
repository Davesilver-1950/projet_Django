<template>
  <div class="card">
    <h3>Comparaison Avant / Après modification du réseau</h3>
    <p class="muted">
      Sélectionnez un calcul enregistré pour comparer son parcours avec un autre calcul ou recalculer avec l'état courant du réseau (ex. après fermeture d'un tronçon).
    </p>

    <div class="form-grid">
      <div class="form-group">
        <label for="calcul-avant">Calcul de référence (Avant)</label>
        <select id="calcul-avant" v-model="calculAvantId" class="select">
          <option disabled value="">Choisir un calcul...</option>
          <option v-for="c in calculs" :key="c.id" :value="c.id">
            #{{ c.id }} — {{ c.libelle || `${c.origine_nom} → ${c.destination_nom}` }}
            ({{ c.critere }}, {{ c.type_vehicule }})
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="calcul-apres">Calcul à comparer (optionnel si recalcul direct)</label>
        <select id="calcul-apres" v-model="calculApresId" class="select">
          <option value="">Recalculer en direct sur le réseau actuel</option>
          <option v-for="c in calculs" :key="c.id" :value="c.id">
            #{{ c.id }} — {{ c.libelle || `${c.origine_nom} → ${c.destination_nom}` }}
            ({{ c.critere }}, {{ c.type_vehicule }})
          </option>
        </select>
      </div>
    </div>

    <div class="btn-row">
      <button
        type="button"
        class="btn btn-primary"
        :disabled="!calculAvantId || loading"
        @click="lancerComparaison(true)"
      >
        {{ loading ? "Comparaison..." : "Recalculer sur le réseau actuel et comparer" }}
      </button>
      <button
        v-if="calculApresId"
        type="button"
        class="btn btn-secondary"
        :disabled="!calculAvantId || loading"
        @click="lancerComparaison(false)"
      >
        Comparer les deux calculs sélectionnés
      </button>
    </div>

    <div v-if="erreur" class="alert-error" role="alert">
      <strong>{{ erreur.code }}</strong> — {{ erreur.message }}
    </div>

    <div v-if="comparaison" class="result-section">
      <div class="explication-box">
        <strong>Analyse de l'écart :</strong> {{ comparaison.explication }}
      </div>

      <div class="deltas-grid">
        <div class="kpi">
          <span class="kpi-label">Écart distance</span>
          <strong>
            {{ formatSigned(comparaison.ecarts.distance_km) }} km
            ({{ formatSigned(comparaison.ecarts.distance_pct) }} %)
          </strong>
        </div>
        <div class="kpi">
          <span class="kpi-label">Écart temps estimé</span>
          <strong>
            {{ formatSigned(comparaison.ecarts.temps_estime_min) }} min
            ({{ formatSigned(comparaison.ecarts.temps_pct) }} %)
          </strong>
        </div>
        <div class="kpi">
          <span class="kpi-label">Écart coût pondéré</span>
          <strong>
            {{ formatSigned(comparaison.ecarts.cout_estime_fcfa) }} FCFA
            ({{ formatSigned(comparaison.ecarts.cout_pct) }} %)
          </strong>
        </div>
      </div>

      <div v-if="comparaison.troncons_evites.length" class="evites-box">
        <strong>Tronçons évités :</strong>
        <ul>
          <li v-for="t in comparaison.troncons_evites" :key="t.troncon_id">
            {{ t.libelle }} — <span class="badge badge-warning">{{ t.raison }}</span>
          </li>
        </ul>
      </div>

      <div class="side-by-side">
        <div class="panel">
          <h4>Avant (#{{ comparaison.avant.calcul_id }})</h4>
          <p>{{ comparaison.avant.noeuds_traverses_noms.join(" → ") }}</p>
          <p class="metrics">
            {{ comparaison.avant.distance_totale_km.toFixed(2) }} km ·
            {{ comparaison.avant.temps_total_min.toFixed(2) }} min ·
            {{ comparaison.avant.cout_total_fcfa.toFixed(2) }} FCFA
          </p>
        </div>

        <div class="panel">
          <h4>Après (#{{ comparaison.apres.calcul_id }})</h4>
          <p>{{ comparaison.apres.noeuds_traverses_noms.join(" → ") }}</p>
          <p class="metrics">
            {{ comparaison.apres.distance_totale_km.toFixed(2) }} km ·
            {{ comparaison.apres.temps_total_min.toFixed(2) }} min ·
            {{ comparaison.apres.cout_total_fcfa.toFixed(2) }} FCFA
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { extractApiError } from "../../services/api";
import { comparerAvantApres } from "../../services/itinerairesService";

defineProps({
  calculs: { type: Array, required: true },
});

const emit = defineEmits(["refresh-historique"]);

const calculAvantId = ref("");
const calculApresId = ref("");
const loading = ref(false);
const erreur = ref(null);
const comparaison = ref(null);

async function lancerComparaison(forcerRecalcul) {
  loading.value = true;
  erreur.value = null;
  try {
    comparaison.value = await comparerAvantApres({
      calcul_avant_id: calculAvantId.value,
      calcul_apres_id: forcerRecalcul ? null : calculApresId.value,
      recalculer: forcerRecalcul || !calculApresId.value,
    });
    if (forcerRecalcul || !calculApresId.value) {
      emit("refresh-historique");
    }
  } catch (err) {
    erreur.value = extractApiError(err);
  } finally {
    loading.value = false;
  }
}

function formatSigned(val) {
  const num = Number(val || 0);
  return `${num > 0 ? "+" : ""}${num.toFixed(2)}`;
}
</script>

<style scoped>
.muted {
  color: var(--muted);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.9rem;
}

.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-bottom: 1rem;
}

.result-section {
  margin-top: 1rem;
}

.explication-box {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 0.85rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.deltas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.kpi {
  background: var(--surface-alt);
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 0.78rem;
  color: var(--muted);
}

.evites-box {
  margin-bottom: 1rem;
}

.side-by-side {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.9rem;
}

.panel {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.9rem;
}

.panel h4 {
  margin-top: 0;
}

.metrics {
  font-weight: 600;
  margin-bottom: 0;
}
</style>
