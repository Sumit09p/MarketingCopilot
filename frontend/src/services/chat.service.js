import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

function auth() {
  return { token: getStoredToken() };
}

export function sendMessage(payload) {
  return apiClient.post("/api/chat/message", payload, auth());
}

export function sendAgentMessage(payload) {
  return apiClient.post("/api/chat/agent", payload, auth());
}
