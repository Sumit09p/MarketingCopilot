import { apiClient } from "./apiClient";

export function sendAgentMessage(payload) {
  return apiClient.post("/api/chat/agent", payload);
}