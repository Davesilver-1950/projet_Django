<template>
  <section class="home-grid">
    <div class="card">
      <h1>SmartRoute CM</h1>
      <p class="subtitle">
        Aide à la planification des tournées de livraison sur un réseau routier simplifié et fictif.
      </p>

      <div class="health-box">
        <strong>État de l'API Django :</strong>
        <span v-if="loading" class="badge">Vérification...</span>
        <span v-else-if="health?.status === 'ok'" class="badge badge-success">
          En ligne · Base {{ health.database }} · v{{ health.version }}
        </span>
        <span v-else class="badge badge-danger">
          Hors ligne ({{ errorMsg || "serveur inaccessible" }})
        </span>
      </div>

      <div class="actions">
        <router-link v-if="!isAuthenticated" to="/login" class="btn btn-primary">
          Se connecter
        </router-link>
        <router-link v-else to="/itineraires" class="btn btn-primary">
          Ouvrir le calculateur d'itinéraires
        </router-link>
      </div>
    </div>

    <div class="card">
      <h2>Modules de l'équipe</h2>
      <ul class="module-list">
        <li><strong>Itinéraires (Yannis)</strong> — Pondération, Dijkstra multi-critères et comparaisons</li>
        <li><strong>Authentification (Sandra)</strong> — Comptes, rôles et sécurité JWT</li>
        <li><strong>Réseau (Serena)</strong> — Points, tronçons, congestion, fermeture/réouverture</li>
        <li><strong>Flotte & Colis (Daphné)</strong> — Véhicules, livreurs, points de livraison, colis</li>
        <li><strong>Tournées (Larue)</strong> — Planification, étapes ordonnées et vue livreur mobile</li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "../services/api";
import { useAuth } from "../stores/auth";

const { isAuthenticated } = useAuth();
const loading = ref(true);
const health = ref(null);
const errorMsg = ref("");

onMounted(async () => {
  try {
    const res = await api.get("/health/");
    health.value = res.data;
  } catch (err) {
    errorMsg.value = err?.message || "erreur réseau";
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.home-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.subtitle {
  color: var(--muted);
}

.health-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin: 1rem 0;
}

.actions {
  margin-top: 1rem;
}

.module-list {
  padding-left: 1.2rem;
  margin: 0.5rem 0 0;
}

.module-list li {
  margin-bottom: 0.45rem;
}
</style>
