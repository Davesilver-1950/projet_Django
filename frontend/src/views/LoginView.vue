<template>
  <div class="login-wrapper">
    <form class="card login-card" @submit.prevent="submit">
      <h1>Connexion</h1>
      <p class="muted">Authentification JWT sécurisée SmartRoute CM.</p>

      <div v-if="errorMessage" class="alert-error" role="alert">
        {{ errorMessage }}
      </div>

      <div class="form-group">
        <label for="username">Identifiant</label>
        <input
          id="username"
          v-model.trim="username"
          type="text"
          class="input"
          autocomplete="username"
          required
        />
      </div>

      <div class="form-group">
        <label for="password">Mot de passe</label>
        <input
          id="password"
          v-model="password"
          type="password"
          class="input"
          autocomplete="current-password"
          required
        />
      </div>

      <button type="submit" class="btn btn-primary full-width" :disabled="submitting">
        {{ submitting ? "Connexion..." : "Se connecter" }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { extractApiError } from "../services/api";
import { useAuth } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const { login } = useAuth();

const username = ref("");
const password = ref("");
const submitting = ref(false);
const errorMessage = ref("");

async function submit() {
  submitting.value = true;
  errorMessage.value = "";
  try {
    await login(username.value, password.value);
    const redirect = route.query.redirect || "/";
    router.push(String(redirect));
  } catch (err) {
    errorMessage.value = extractApiError(err).message;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  padding-top: 1.5rem;
}

.login-card {
  width: 100%;
  max-width: 420px;
}

.muted {
  color: var(--muted);
  margin-top: -0.25rem;
  margin-bottom: 1rem;
}

.full-width {
  width: 100%;
}
</style>
