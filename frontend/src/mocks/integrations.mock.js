import { delay } from "./delay";
import integrationsData from "./data/integrations.json";

export async function listIntegrations() {
  await delay();
  return integrationsData.map((item) => ({ ...item }));
}

export async function connectIntegration() {
  await delay();
  return { status: "NOT_CONNECTED" };
}
