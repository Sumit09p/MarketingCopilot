import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function listCampaigns() {
  return apiClient.get("/api/campaigns", auth());
}

export function createCampaign(payload) {
  return apiClient.post("/api/campaigns", payload, auth());
}

export function getCampaign(campaignId) {
  return apiClient.get(`/api/campaigns/${campaignId}`, auth());
}

export function runCampaign(campaignId, payload) {
  return apiClient.post(`/api/campaigns/${campaignId}/run`, payload, auth());
}

export function getCampaignRun(campaignId, runId) {
  return apiClient.get(`/api/campaigns/${campaignId}/runs/${runId}`, auth());
}
