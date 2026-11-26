<template>
  <div class="app-shell">
    <div class="fictif-banner" role="note">
      Simulation pédagogique — Toutes les données affichées (réseau de Douala, temps, coûts en FCFA, comptes) sont fictives.
    </div>

    <header class="topbar">
      <div class="container topbar-inner">
        <router-link to="/" class="brand">SmartRoute CM</router-link>

        <nav class="nav-links" aria-label="Navigation principale">
          <router-link to="/">Accueil</router-link>
          <router-link v-if="isAuthenticated" to="/itineraires">Itinéraires</router-link>
          <router-link v-if="isAuthenticated" to="/reseau">Réseau</router-link>
          <router-link v-if="isAuthenticated" to="/flotte">Flotte</router-link>
          <router-link v-if="isAuthenticated" to="/tournees">Tournées</router-link>
          <router-link v-if="role === 'admin'" to="/utilisateurs">Comptes</router-link>
        </nav>

        <div class="auth-box">
          <template v-if="isAuthenticated && user">
            <span class="badge">{{ user.username }} · {{ user.role_libelle || user.role }}</span>
            <button type="button" class="btn btn-secondary btn-sm" @click="handleLogout">
              Déconnexion
            </button>
          </template>
          <router-link v-else to="/login" class="btn btn-primary btn-sm">
            Connexion
          </router-link>
        </div>
      </div>
    </header>

    <main class="container main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "./stores/auth";

const router = useRouter();
const { user, isAuthenticated, role, fetchMe, logout } = useAuth();

onMounted(() => {
  if (isAuthenticated.value && !user.value) {
    fetchMe().catch(() => logout());
  }
});

function handleLogout() {
  logout();
  router.push("/login");
}
</script>

<style scoped>
.fictif-banner {
  background: #1e293b;
  color: #f8fafc;
  text-align: center;
  font-size: 0.82rem;
  padding: 0.4rem 0.75rem;
}

.topbar {
  background: #ffffff;
  border-bottom: 1px solid var(--border);
}

.topbar-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.brand {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--primary);
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  font-size: 0.92rem;
  font-weight: 500;
}

.nav-links a.router-link-active {
  color: var(--primary);
  font-weight: 700;
}

.auth-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.84rem;
}

.main-content {
  padding-top: 1.25rem;
  padding-bottom: 2.5rem;
}
</style>
