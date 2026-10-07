import { delay } from "./delay";

export async function getAgentRun(runId) {
  await delay();
  return {
    run_id: runId,
    agent: "research",
    status: "COMPLETED",
    started_at: "2026-09-23T10:00:00Z",
    completed_at: "2026-09-23T10:02:00Z",
    result: {},
    confidence: 0.92,
    error: null,
  };
}
