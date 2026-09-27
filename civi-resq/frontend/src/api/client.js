import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("civiresq_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const zonesApi = {
  list: (params = {}) => api.get("/api/zones", { params }).then((r) => r.data),
  detail: (id) => api.get(`/api/zones/${id}`).then((r) => r.data),
  reassess: (id) => api.post(`/api/zones/${id}/assess`).then((r) => r.data),
  uploadCsv: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post("/api/zones/upload-csv", form, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
};

export const analyticsApi = {
  dashboard: () => api.get("/api/analytics/dashboard").then((r) => r.data),
  riskDistribution: () => api.get("/api/analytics/risk-distribution").then((r) => r.data),
};

export const simulateApi = {
  run: (zoneId, modifiedParams) =>
    api.post("/api/simulate", { zone_id: zoneId, modified_params: modifiedParams }).then((r) => r.data),
};

export const assistantApi = {
  ask: (question, zoneId) =>
    api.post("/api/assistant/ask", { question, zone_id: zoneId }).then((r) => r.data),
};

export const authApi = {
  login: (email, password) => api.post("/api/auth/login", { email, password }).then((r) => r.data),
  register: (payload) => api.post("/api/auth/register", payload).then((r) => r.data),
};

export default api;
