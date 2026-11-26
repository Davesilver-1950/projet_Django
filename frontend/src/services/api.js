import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem("smartroute_access");
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/login/") &&
      !originalRequest.url?.includes("/auth/refresh/")
    ) {
      const refreshToken = localStorage.getItem("smartroute_refresh");
      if (refreshToken) {
        originalRequest._retry = true;
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem("smartroute_access", res.data.access);
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("smartroute_access");
          localStorage.removeItem("smartroute_refresh");
          localStorage.removeItem("smartroute_user");
        }
      }
    }
    return Promise.reject(error);
  }
);

export function extractApiError(error) {
  const payload = error?.response?.data;
  if (payload && typeof payload === "object") {
    return {
      status: error.response?.status,
      code: payload.code || "ERREUR_API",
      message: payload.message || "Une erreur est survenue.",
      details: payload.details || null,
    };
  }
  return {
    status: error?.response?.status || 0,
    code: "RESEAU_INDISPONIBLE",
    message: "Impossible de joindre l'API SmartRoute CM.",
    details: null,
  };
}

export default api;
