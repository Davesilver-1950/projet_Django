import { computed, reactive } from "vue";
import api from "../services/api";

const storedUser = localStorage.getItem("smartroute_user");

const state = reactive({
  user: storedUser ? JSON.parse(storedUser) : null,
  accessToken: localStorage.getItem("smartroute_access") || "",
});

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(state.accessToken));
  const role = computed(() => state.user?.role || null);

  async function login(username, password) {
    const response = await api.post("/auth/login/", { username, password });
    const { access, refresh, user } = response.data;
    state.accessToken = access;
    state.user = user;
    localStorage.setItem("smartroute_access", access);
    localStorage.setItem("smartroute_refresh", refresh);
    localStorage.setItem("smartroute_user", JSON.stringify(user));
    return user;
  }

  async function fetchMe() {
    if (!state.accessToken) return null;
    const response = await api.get("/auth/me/");
    state.user = response.data;
    localStorage.setItem("smartroute_user", JSON.stringify(response.data));
    return response.data;
  }

  function logout() {
    state.accessToken = "";
    state.user = null;
    localStorage.removeItem("smartroute_access");
    localStorage.removeItem("smartroute_refresh");
    localStorage.removeItem("smartroute_user");
  }

  return {
    state,
    user: computed(() => state.user),
    isAuthenticated,
    role,
    login,
    fetchMe,
    logout,
  };
}
