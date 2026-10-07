import { delay } from "./delay";
import analyticsData from "./data/analytics.json";

export async function getSummary() {
  await delay();
  return {
    ...analyticsData.summary,
    is_sample_data: true,
    label: analyticsData.label,
  };
}

export async function getTimeseries() {
  await delay();
  return analyticsData.timeseries.map((item) => ({ ...item }));
}

export async function getInsights() {
  await delay();
  return { ...analyticsData.insights };
}
