<template>
  <div class="card">
    <div class="header-row">
      <h3>Tableau comparatif des 3 critères</h3>
      <span class="badge">Données fictives</span>
    </div>

    <p v-if="synthese" class="synthese">{{ synthese }}</p>

    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th>Critère</th>
            <th>Distance (km)</th>
            <th>Temps (min)</th>
            <th>Coût (FCFA)</th>
            <th>Tronçons</th>
            <th>Parcours</th>
            <th>Écart vs distance</th>
            <th>Détails</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="ligne in tableau"
            :key="ligne.critere"
            :class="{ selected: ligne.critere === critereSelectionne }"
          >
            <td><strong>{{ libelleCritere(ligne.critere) }}</strong></td>
            <td>{{ ligne.distance_totale_km.toFixed(2) }}</td>
            <td>{{ ligne.temps_total_min.toFixed(2) }}</td>
            <td>{{ ligne.cout_total_fcfa.toFixed(2) }}</td>
            <td>{{ ligne.nombre_troncons }}</td>
            <td class="path-cell">{{ ligne.noeuds_traverses_noms.join(" → ") }}</td>
            <td>
              <span v-if="ligne.critere === 'distance'" class="badge">Référence</span>
              <span v-else>
                {{ formatDelta(ligne.ecart_vs_distance_km, "km") }},
                {{ formatDelta(ligne.ecart_vs_distance_temps_min, "min") }}
              </span>
            </td>
            <td>
              <button
                type="button"
                class="btn btn-secondary btn-xs"
                @click="$emit('select-critere', ligne.critere)"
              >
                {{ ligne.critere === critereSelectionne ? "Affiché" : "Voir étapes" }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tableau: { type: Array, required: true },
  synthese: { type: String, default: "" },
  critereSelectionne: { type: String, default: "distance" },
});

defineEmits(["select-critere"]);

function libelleCritere(critere) {
  if (critere === "distance") return "Distance min.";
  if (critere === "temps") return "Temps estimé min.";
  if (critere === "cout") return "Coût pondéré min.";
  return critere;
}

function formatDelta(val, unite) {
  const num = Number(val || 0);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(2)} ${unite}`;
}
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.header-row h3 {
  margin: 0;
}

.synthese {
  background: var(--surface-alt);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.selected {
  background: #eff6ff;
}

.path-cell {
  max-width: 260px;
}

.btn-xs {
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
}
</style>
