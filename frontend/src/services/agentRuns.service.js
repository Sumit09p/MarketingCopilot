import { apiClient } from "./apiClient";
import { getStoredToken } from "../utils/storage";

export function getAgentRun(runId) {
  return apiClient.get(`/api/agent-runs/${runId}`, {
    token: getStoredToken(),
  });
}
