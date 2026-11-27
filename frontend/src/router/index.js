import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import ItinerairesView from "../views/ItinerairesView.vue";
import LoginView from "../views/LoginView.vue";
import ModulePlaceholderView from "../views/ModulePlaceholderView.vue";
import UtilisateursView from "../views/UtilisateursView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/login", name: "login", component: LoginView },
  {
    path: "/itineraires",
    name: "itineraires",
    component: ItinerairesView,
    meta: { requiresAuth: true },
  },
  {
    path: "/reseau",
    name: "reseau",
    component: ModulePlaceholderView,
    meta: {
      requiresAuth: true,
      title: "Réseau routier fictif",
      owner: "Serena",
      branch: "feat/serena-reseau",
    },
  },
  {
    path: "/flotte",
    name: "flotte",
    component: ModulePlaceholderView,
    meta: {
      requiresAuth: true,
      title: "Flotte, points de livraison et colis",
      owner: "Daphné",
      branch: "feat/daphne-flotte",
    },
  },
  {
    path: "/tournees",
    name: "tournees",
    component: ModulePlaceholderView,
    meta: {
      requiresAuth: true,
      title: "Tournées et étapes",
      owner: "Larue",
      branch: "feat/larue-tournees",
    },
  },
  {
    path: "/utilisateurs",
    name: "utilisateurs",
    component: UtilisateursView,
    meta: { requiresAuth: true, roles: ["admin"] },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = localStorage.getItem("smartroute_access");
  if (to.meta.requiresAuth && !token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  // Garde par rôle (confort d'affichage : le vrai contrôle reste côté serveur).
  if (to.meta.roles) {
    let role = null;
    try {
      role = JSON.parse(localStorage.getItem("smartroute_user"))?.role ?? null;
    } catch {
      role = null;
    }
    if (!to.meta.roles.includes(role)) {
      return { name: "home" };
    }
  }
  return true;
});

export default router;