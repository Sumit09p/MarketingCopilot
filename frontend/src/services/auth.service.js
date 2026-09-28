import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function withAuth(options = {}) {
  return { ...options, token: options.token ?? getStoredToken() };
}

export function register(payload) {
  return apiClient.post("/api/auth/register", payload);
}

export function login(payload) {
  return apiClient.post("/api/auth/login", payload);
}

export function getCurrentUser() {
  return apiClient.get("/api/auth/me", withAuth());
}

export function logout() {
  return Promise.resolve(null);
}
