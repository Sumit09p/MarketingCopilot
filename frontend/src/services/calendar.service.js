import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function getCalendar(campaignId) {
  return apiClient.get(`/api/campaigns/${campaignId}/calendar`, auth());
}

export function addCalendarItem(campaignId, payload) {
  return apiClient.post(`/api/campaigns/${campaignId}/calendar`, payload, auth());
}
