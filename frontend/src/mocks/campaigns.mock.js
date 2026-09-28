import { delay } from "./delay";
import campaignsData from "./data/campaigns.json";
import runsData from "./data/runs.json";

const campaigns = JSON.parse(JSON.stringify(campaignsData));
const runs = JSON.parse(JSON.stringify(runsData));

function listItem(campaign) {
  return {
    id: campaign.id,
    name: campaign.name,
    objective: campaign.objective,
    product: campaign.product,
    audience: campaign.audience,
    platforms: campaign.platforms,
    budget: campaign.budget,
    duration: campaign.duration,
    status: campaign.status,
    created_at: campaign.created_at,
  };
}

function publicRun(run) {
  if (!run?.started_ms) {
    const clone = JSON.parse(JSON.stringify(run));
    delete clone.started_ms;
    delete clone.instruction;
    return clone;
  }

  const elapsed = Date.now() - run.started_ms;
  const completedCount = Math.min(run.tasks.length, Math.floor(elapsed / 1500));
  const tasks = run.tasks.map((task, index) => {
    if (index < completedCount) return { ...task, status: "COMPLETED" };
    if (index === completedCount) return { ...task, status: "RUNNING" };
    return { ...task, status: "PENDING" };
  });

  let status = "RUNNING";
  if (completedCount >= run.tasks.length) status = "COMPLETED";

  return {
    run_id: run.run_id,
    campaign_id: run.campaign_id,
    status,
    tasks,
  };
}

export async function listCampaigns() {
  await delay();
  return campaigns.map(listItem);
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
  const campaign = campaigns.find((item) => item.id === campaignId);
  return campaign ? JSON.parse(JSON.stringify(campaign)) : null;
}

export async function runCampaign(campaignId, payload) {
  await delay();
  const run = {
    run_id: `run_${Date.now()}`,
    campaign_id: campaignId,
    status: "RUNNING",
    started_ms: Date.now(),
    instruction: payload?.instruction,
    tasks: [
      { id: "research_1", agent: "research", status: "PENDING" },
      { id: "competitor_1", agent: "competitor", status: "PENDING" },
      { id: "seo_1", agent: "seo", status: "PENDING" },
      { id: "content_1", agent: "content", status: "PENDING" },
      { id: "image_1", agent: "image", status: "PENDING" },
      { id: "analytics_1", agent: "analytics", status: "PENDING" },
    ],
  };
  runs.unshift(run);
  return { campaign_id: campaignId, run_id: run.run_id, status: "STARTED" };
}

export async function getCampaignRun(campaignId, runId) {
  await delay();
  const run =
    runs.find((item) => item.run_id === runId && item.campaign_id === campaignId) ??
    runs.find((item) => item.run_id === runId);
  if (!run) return null;
  return publicRun(run);
}
