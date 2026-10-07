import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function getSummary() {
  return apiClient.get("/api/analytics/summary", auth());
}

export function getTimeseries(params = {}) {
  const query = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
    )
  ).toString();
  const path = query ? `/api/analytics/timeseries?${query}` : "/api/analytics/timeseries";
  return apiClient.get(path, auth());
}

export function getInsights(payload) {
  return apiClient.post("/api/analytics/insights", payload, auth());
}
