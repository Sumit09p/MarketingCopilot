import { delay } from "./delay";
import campaignsData from "./data/campaigns.json";
import runsData from "./data/runs.json";

const campaigns = JSON.parse(JSON.stringify(campaignsData));
const runs = JSON.parse(JSON.stringify(runsData));

export async function listCampaigns() {
  await delay();
  return campaigns.map(({ id, name, objective, status, created_at }) => ({
    id,
    name,
    objective,
    status,
    created_at,
  }));
}

export async function createCampaign(payload) {
  await delay();
  const campaign = {
    id: `campaign_${Date.now()}`,
    name: payload.name,
    objective: payload.objective,
    product: payload.product,
    audience: payload.audience,
    platforms: payload.platforms ?? [],
    budget: payload.budget,
    duration: payload.duration,
    status: "DRAFT",
    created_at: new Date().toISOString(),
    research: null,
    competitor_analysis: null,
    seo: null,
    content: null,
    creatives: [],
    calendar: [],
    analytics: null,
  };
  campaigns.unshift(campaign);
  return { id: campaign.id, name: campaign.name, status: campaign.status };
}

export async function getCampaign(campaignId) {
  await delay();
  return JSON.parse(JSON.stringify(campaigns.find((item) => item.id === campaignId) ?? null));
}

export async function runCampaign(campaignId) {
  await delay();
  const run = {
    run_id: `run_${Date.now()}`,
    campaign_id: campaignId,
    status: "STARTED",
    tasks: [
      { id: "research_1", agent: "research", status: "PENDING" },
      { id: "competitor_1", agent: "competitor", status: "PENDING" },
      { id: "content_1", agent: "content", status: "PENDING" },
    ],
  };
  runs.unshift(run);
  return { campaign_id: campaignId, run_id: run.run_id, status: "STARTED" };
}

export async function getCampaignRun(campaignId, runId) {
  await delay();
  const run = runs.find((item) => item.run_id === runId && item.campaign_id === campaignId) ?? runs[0];
  return JSON.parse(JSON.stringify(run));
}
