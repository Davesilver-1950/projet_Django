<template>
  <section class="card">
    <h1>Comptes et rôles</h1>
    <p class="muted">Gestion des comptes (Administrateur). Données fictives uniquement.</p>

    <div v-if="message" class="alert-error" role="alert">{{ message }}</div>

    <form class="form-grid" @submit.prevent="creer">
      <h2>Nouveau compte</h2>
      <input v-model.trim="form.username" class="input" placeholder="Identifiant" required />
      <input v-model.trim="form.email" type="email" class="input" placeholder="E-mail fictif" required />
      <input v-model="form.password" type="password" class="input" placeholder="Mot de passe (8 caractères min.)" required />
      <select v-model="form.role" class="input">
        <option value="admin">Administrateur</option>
        <option value="gestionnaire">Gestionnaire logistique</option>
        <option value="livreur">Livreur</option>
      </select>
      <template v-if="form.role === 'livreur'">
        <input v-model.trim="form.nom" class="input" placeholder="Nom complet fictif" required />
        <input v-model.trim="form.telephone_fictif" class="input" placeholder="Téléphone fictif" required />
      </template>
      <button type="submit" class="btn btn-primary" :disabled="envoi">Créer le compte</button>
    </form>

    <table class="table">
      <thead>
        <tr>
          <th>Identifiant</th>
          <th>E-mail</th>
          <th>Rôle</th>
          <th>Actif</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in comptes" :key="u.id">
          <td>{{ u.username }}</td>
          <td>{{ u.email }}</td>
          <td>{{ u.role_libelle }}</td>
          <td>{{ u.is_active ? "Oui" : "Non" }}</td>
          <td>
            <button class="btn btn-secondary btn-sm" @click="basculerActif(u)">
              {{ u.is_active ? "Désactiver" : "Activer" }}
            </button>
            <button class="btn btn-secondary btn-sm" @click="supprimer(u)">Supprimer</button>
          </td>
        </tr>
        <tr v-if="!comptes.length">
          <td colspan="5" class="muted">Aucun compte.</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import api, { extractApiError } from "../services/api";

const comptes = ref([]);
const message = ref("");
const envoi = ref(false);
const form = reactive({
  username: "",
  email: "",
  password: "",
  role: "livreur",
  nom: "",
  telephone_fictif: "",
});

function erreur(err) {
  const e = extractApiError(err);
  const d = e.details && typeof e.details === "object" ? Object.values(e.details).flat().join(" ") : "";
  message.value = d ? `${e.message} ${d}` : e.message;
}

async function charger() {
  try {
    const { data } = await api.get("/auth/utilisateurs/");
    comptes.value = Array.isArray(data) ? data : data.results || [];
  } catch (err) {
    erreur(err);
  }
}

async function creer() {
  envoi.value = true;
  message.value = "";
  try {
    // nom et téléphone ne concernent que les livreurs : l'API refuse les champs vides.
    const { nom, telephone_fictif, ...compte } = form;
    await api.post(
      "/auth/utilisateurs/",
      form.role === "livreur" ? { ...compte, nom, telephone_fictif } : compte
    );
    Object.assign(form, { username: "", email: "", password: "", nom: "", telephone_fictif: "" });
    await charger();
  } catch (err) {
    erreur(err);
  } finally {
    envoi.value = false;
  }
}

async function basculerActif(u) {
  message.value = "";
  try {
    await api.patch(`/auth/utilisateurs/${u.id}/`, { is_active: !u.is_active });
    await charger();
  } catch (err) {
    erreur(err);
  }
}

async function supprimer(u) {
  if (!window.confirm(`Supprimer le compte ${u.username} ?`)) return;
  message.value = "";
  try {
    await api.delete(`/auth/utilisateurs/${u.id}/`);
    await charger();
  } catch (err) {
    erreur(err);
  }
}

onMounted(charger);
</script>

<style scoped>
.muted {
  color: var(--muted);
}
.form-grid {
  display: grid;
  gap: 0.5rem;
  max-width: 420px;
  margin: 1rem 0 1.5rem;
}
.table {
  width: 100%;
  border-collapse: collapse;
}
.table th,
.table td {
  text-align: left;
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}
</style>