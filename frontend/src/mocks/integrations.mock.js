import { delay } from "./delay";
import integrationsData from "./data/integrations.json";

const integrations = JSON.parse(JSON.stringify(integrationsData));

export async function listIntegrations() {
  await delay();
  return integrations.map((item) => ({ ...item }));
}

export async function connectIntegration(provider) {
  await delay();
  const current = integrations.find((item) => item.provider === provider);
  return {
    provider,
    status: current?.status || "NOT_CONNECTED",
  };
}
