import { delay } from "./delay";
import calendarData from "./data/calendar.json";

const calendarByCampaign = JSON.parse(JSON.stringify(calendarData));

export async function getCalendar(campaignId) {
  await delay();
  return (calendarByCampaign[campaignId] ?? []).map((item) => ({ ...item }));
}

export async function updateCalendarItem(campaignId, itemId, payload) {
  await delay();
  const currentItems = calendarByCampaign[campaignId] ?? [];
  const index = currentItems.findIndex((item) => item.id === itemId);
  if (index < 0) throw new Error("Calendar item was not found.");
  const updated = { ...currentItems[index], ...payload, id: itemId };
  const targetCampaignId = payload.campaignId || campaignId;
  if (targetCampaignId !== campaignId) {
    calendarByCampaign[campaignId] = currentItems.filter((item) => item.id !== itemId);
    calendarByCampaign[targetCampaignId] = calendarByCampaign[targetCampaignId] ?? [];
    calendarByCampaign[targetCampaignId].push(updated);
  } else {
    calendarByCampaign[campaignId] = currentItems.map((item, itemIndex) => itemIndex === index ? updated : item);
  }
  return updated;
}

export async function addCalendarItem(campaignId, payload) {
  await delay();
  const item = { id: `calendar_item_${Date.now()}`, ...payload };
  calendarByCampaign[campaignId] = calendarByCampaign[campaignId] ?? [];
  calendarByCampaign[campaignId].push(item);
  return { id: item.id };
}
