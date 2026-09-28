import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function getBrand() {
  return apiClient.get("/api/brand", auth());
}

export function updateBrand(payload) {
  return apiClient.put("/api/brand", payload, auth());
}
