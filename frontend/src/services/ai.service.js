import { apiClient } from "./apiClient";

export async function generateAI(prompt, systemPrompt = null) {
  return apiClient.post("/api/ai/generate", {
    prompt,
    system_prompt: systemPrompt,
  });
}