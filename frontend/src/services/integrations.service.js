import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function listIntegrations() {
  return apiClient.get("/api/integrations", auth());
}

export function connectIntegration(provider) {
  return apiClient.post(`/api/integrations/${provider}/connect`, {}, auth());
}
