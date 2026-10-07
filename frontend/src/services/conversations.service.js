import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function listConversations() {
  return apiClient.get("/api/conversations", auth());
}

export function getConversation(conversationId) {
  return apiClient.get(`/api/conversations/${conversationId}`, auth());
}

export function createConversation(payload) {
  return apiClient.post("/api/conversations", payload, auth());
}

export function renameConversation(conversationId, payload) {
  return apiClient.patch(`/api/conversations/${conversationId}`, payload, auth());
}

export function deleteConversation(conversationId) {
  return apiClient.delete(`/api/conversations/${conversationId}`, auth());
}
