import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import ModulePlaceholderView from "../views/ModulePlaceholderView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/login", name: "login", component: LoginView },
  {
    path: "/itineraires",
    name: "itineraires",
    component: ModulePlaceholderView,
    meta: {
      requiresAuth: true,
      title: "Moteur d'itinéraires (Dijkstra)",
      owner: "Yannis",
      branch: "feat/yannis-dijkstra",
    },
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
    component: ModulePlaceholderView,
    meta: {
      requiresAuth: true,
      title: "Comptes et rôles",
      owner: "Sandra",
      branch: "feat/sandra-auth",
    },
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
  return true;
});

export default router;
