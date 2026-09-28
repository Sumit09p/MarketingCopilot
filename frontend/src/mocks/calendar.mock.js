import { delay } from "./delay";
import calendarData from "./data/calendar.json";

const calendarByCampaign = JSON.parse(JSON.stringify(calendarData));

export async function getCalendar(campaignId) {
  await delay();
  return (calendarByCampaign[campaignId] ?? []).map((item) => ({ ...item }));
}

export async function addCalendarItem(campaignId, payload) {
  await delay();
  const item = { id: `calendar_item_${Date.now()}`, ...payload };
  calendarByCampaign[campaignId] = calendarByCampaign[campaignId] ?? [];
  calendarByCampaign[campaignId].push(item);
  return { id: item.id };
}
