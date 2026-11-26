<template>
  <div class="card">
    <div class="header-row">
      <h3>{{ titre }}</h3>
      <span v-if="resultat.duree_calcul_ms !== undefined" class="badge">
        Calculé en {{ resultat.duree_calcul_ms }} ms
      </span>
    </div>

    <div class="totaux-grid">
      <div class="kpi">
        <span class="kpi-label">Distance totale</span>
        <strong>{{ resultat.distance_totale_km.toFixed(2) }} km</strong>
      </div>
      <div class="kpi">
        <span class="kpi-label">Temps estimé</span>
        <strong>{{ resultat.temps_total_min.toFixed(2) }} min</strong>
      </div>
      <div class="kpi">
        <span class="kpi-label">Coût pondéré</span>
        <strong>{{ resultat.cout_total_fcfa.toFixed(2) }} FCFA</strong>
      </div>
      <div class="kpi">
        <span class="kpi-label">Tronçons empruntés</span>
        <strong>{{ resultat.nombre_troncons }}</strong>
      </div>
    </div>

    <p class="parcours-resume">
      <strong>Parcours :</strong> {{ (resultat.noeuds_traverses_noms || []).join(" → ") }}
    </p>

    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Tronçon (quartier & repère)</th>
            <th>Conditions</th>
            <th>Distance / Cumul</th>
            <th>Temps / Cumul</th>
            <th>Coût / Cumul</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="etape in resultat.etapes" :key="etape.rang">
            <td><strong>{{ etape.rang }}</strong></td>
            <td>
              <div>
                <strong>{{ etape.origine_nom }} → {{ etape.destination_nom }}</strong>
                <span v-if="etape.sens_inverse" class="badge">sens inverse</span>
              </div>
              <small class="muted">
                {{ etape.destination_quartier }}
                <template v-if="etape.destination_repere">· {{ etape.destination_repere }}</template>
              </small>
            </td>
            <td>
              <span class="badge" :class="congestionClass(etape.congestion)">
                {{ etape.congestion }}
              </span>
              <span class="badge">{{ etape.etat_route }}</span>
            </td>
            <td>
              {{ etape.distance_km.toFixed(2) }} km
              <br />
              <small class="muted">Cumul : {{ etape.distance_cumulee_km.toFixed(2) }} km</small>
            </td>
            <td>
              {{ etape.temps_estime_min.toFixed(2) }} min
              <br />
              <small class="muted">Cumul : {{ etape.temps_cumule_min.toFixed(2) }} min</small>
            </td>
            <td>
              {{ etape.cout_estime_fcfa.toFixed(2) }} FCFA
              <br />
              <small class="muted">Cumul : {{ etape.cout_cumule_fcfa.toFixed(2) }} FCFA</small>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  resultat: { type: Object, required: true },
  titre: { type: String, default: "Liste ordonnée des étapes" },
});

function congestionClass(niveau) {
  if (niveau === "forte") return "badge-danger";
  if (niveau === "moderee") return "badge-warning";
  return "badge-success";
}
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.9rem;
}

.header-row h3 {
  margin: 0;
}

.totaux-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.kpi {
  background: var(--surface-alt);
  padding: 0.65rem 0.85rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 0.78rem;
  color: var(--muted);
}

.parcours-resume {
  margin-bottom: 0.9rem;
}

.muted {
  color: var(--muted);
}
</style>
