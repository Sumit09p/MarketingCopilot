import { useEffect, useMemo, useState } from "react";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import { calendarService, campaignsService } from "../services";
import { getUserFacingError } from "../utils/errors";
import { formatDate } from "../utils/format";

const TYPES = ["POST"];
const STATUSES = ["DRAFT", "SCHEDULED"];
const PLATFORMS = ["Instagram", "LinkedIn", "Facebook", "YouTube", "X"];

function daysInMonth(year, monthIndex) {
  return new Date(year, monthIndex + 1, 0).getDate();
}

function monthFromEntries(items) {
  const dated = items.find((item) => item?.date);
  if (!dated) return null;
  const next = new Date(`${dated.date}T00:00:00`);
  if (Number.isNaN(next.getTime())) return null;
  return new Date(next.getFullYear(), next.getMonth(), 1);
}

export default function CalendarPage() {
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [campaigns, setCampaigns] = useState([]);
  const [campaignId, setCampaignId] = useState("");
  const [entries, setEntries] = useState([]);
  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [form, setForm] = useState({
    date: "",
    platform: "Instagram",
    type: "POST",
    caption: "",
    status: "DRAFT",
  });
  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  async function loadPage() {
    setStatus("loading");
    setError("");
    try {
      const list = await campaignsService.listCampaigns();
      const items = Array.isArray(list) ? list : [];
      setCampaigns(items);
      const selected = campaignId && items.some((item) => item.id === campaignId) ? campaignId : items[0]?.id || "";
      setCampaignId(selected);
      if (!selected) {
        setEntries([]);
        setStatus("ready");
        return;
      }
      const calendar = await calendarService.getCalendar(selected);
      const calendarItems = Array.isArray(calendar) ? calendar : [];
      setEntries(calendarItems);
      const nextMonth = monthFromEntries(calendarItems);
      if (nextMonth) setCursor(nextMonth);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load the calendar."));
      setStatus("error");
    }
  }

  useEffect(() => {
    loadPage();
  }, []);

  async function loadCalendar(id) {
    setStatus("loading");
    setError("");
    try {
      const calendar = await calendarService.getCalendar(id);
      const calendarItems = Array.isArray(calendar) ? calendar : [];
      setEntries(calendarItems);
      const nextMonth = monthFromEntries(calendarItems);
      if (nextMonth) setCursor(nextMonth);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load calendar entries."));
      setStatus("error");
    }
  }

  const year = cursor.getFullYear();
  const monthIndex = cursor.getMonth();
  const days = daysInMonth(year, monthIndex);
  const firstWeekday = new Date(year, monthIndex, 1).getDay();

  const byDate = useMemo(() => {
    const map = {};
    entries.forEach((entry) => {
      if (!entry.date) return;
      map[entry.date] = map[entry.date] || [];
      map[entry.date].push(entry);
    });
    return map;
  }, [entries]);

  const selectedCampaign = campaigns.find((item) => item.id === campaignId);

  async function onCreate(event) {
    event.preventDefault();
    setFormError("");
    setFormSuccess("");
    if (!campaignId) {
      setFormError("Select a campaign first.");
      return;
    }
    if (!form.date) {
      setFormError("Date is required.");
      return;
    }
    if (!form.platform) {
      setFormError("Platform is required.");
      return;
    }
    if (!form.type) {
      setFormError("Type is required.");
      return;
    }

    setSaving(true);
    try {
      await calendarService.addCalendarItem(campaignId, {
        date: form.date,
        platform: form.platform,
        type: form.type,
        caption: form.caption.trim(),
        status: form.status,
      });
      setFormSuccess("Calendar item scheduled.");
      setForm((current) => ({ ...current, caption: "" }));
      await loadCalendar(campaignId);
    } catch (err) {
      setFormError(getUserFacingError(err, "Could not add that calendar item."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-stack">
      <PageHeader
        title="Calendar"
        description="Campaign content schedule from GET /api/campaigns/{campaign_id}/calendar."
      />

      {status === "loading" ? <LoadingState message="Loading calendar..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={loadPage} /> : null}

      {status === "ready" ? (
        <>
          {campaigns.length === 0 ? (
            <div className="page-card">
              <EmptyState
                title="No campaigns to schedule"
                description="Create a campaign before adding calendar entries. Calendar items belong to a campaign."
              />
            </div>
          ) : (
            <>
              <div className="filter-bar">
                <label className="form-field compact">
                  Campaign
                  <select
                    value={campaignId}
                    onChange={(event) => {
                      const next = event.target.value;
                      setCampaignId(next);
                      loadCalendar(next);
                    }}
                  >
                    {campaigns.map((campaign) => (
                      <option key={campaign.id} value={campaign.id}>
                        {campaign.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="month-nav">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setCursor(new Date(year, monthIndex - 1, 1))}
                  >
                    Previous
                  </button>
                  <strong>
                    {cursor.toLocaleString(undefined, { month: "long", year: "numeric" })}
                  </strong>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setCursor(new Date(year, monthIndex + 1, 1))}
                  >
                    Next
                  </button>
                </div>
              </div>

              <div className="calendar-grid">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <div key={day} className="calendar-dow">
                    {day}
                  </div>
                ))}
                {Array.from({ length: days }, (_, index) => {
                  const day = index + 1;
                  const iso = `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                  const dayEntries = byDate[iso] || [];
                  return (
                    <div
                      key={iso}
                      className="calendar-cell"
                      style={index === 0 ? { gridColumnStart: firstWeekday + 1 } : undefined}
                    >
                      <span className="calendar-day">{day}</span>
                      {dayEntries.map((entry) => (
                        <article key={entry.id} className="calendar-entry">
                          <strong>{entry.type || "Item"}</strong>
                          <span>{entry.platform}</span>
                          <StatusBadge status={entry.status} />
                          {entry.caption ? <p>{entry.caption}</p> : null}
                        </article>
                      ))}
                    </div>
                  );
                })}
              </div>

              <section className="page-card">
                <h2>Schedule list</h2>
                {entries.length === 0 ? (
                  <EmptyState
                    title="No entries this campaign"
                    description="Nothing is scheduled yet for the selected campaign."
                  />
                ) : (
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Campaign</th>
                          <th>Type</th>
                          <th>Platform</th>
                          <th>Status</th>
                          <th>Caption</th>
                        </tr>
                      </thead>
                      <tbody>
                        {entries.map((entry) => (
                          <tr key={entry.id}>
                            <td>{formatDate(entry.date)}</td>
                            <td>{selectedCampaign?.name || campaignId}</td>
                            <td>{entry.type}</td>
                            <td>{entry.platform}</td>
                            <td>
                              <StatusBadge status={entry.status} />
                            </td>
                            <td>{entry.caption || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              <section className="page-card">
                <h2>Add calendar item</h2>
                {formError ? <p className="error-text">{formError}</p> : null}
                {formSuccess ? <p className="success-text">{formSuccess}</p> : null}
                <form className="stack-form" onSubmit={onCreate}>
                  <div className="form-grid">
                    <div className="form-field">
                      <label htmlFor="cal_date">Date</label>
                      <input
                        id="cal_date"
                        type="date"
                        value={form.date}
                        onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))}
                      />
                    </div>
                    <div className="form-field">
                      <label htmlFor="cal_platform">Platform</label>
                      <select
                        id="cal_platform"
                        value={form.platform}
                        onChange={(event) => setForm((current) => ({ ...current, platform: event.target.value }))}
                      >
                        {PLATFORMS.map((platform) => (
                          <option key={platform} value={platform}>
                            {platform}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-field">
                      <label htmlFor="cal_type">Type</label>
                      <select
                        id="cal_type"
                        value={form.type}
                        onChange={(event) => setForm((current) => ({ ...current, type: event.target.value }))}
                      >
                        {TYPES.map((type) => (
                          <option key={type} value={type}>
                            {type}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-field">
                      <label htmlFor="cal_status">Status</label>
                      <select
                        id="cal_status"
                        value={form.status}
                        onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
                      >
                        {STATUSES.map((item) => (
                          <option key={item} value={item}>
                            {item}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="form-field">
                    <label htmlFor="cal_caption">Caption</label>
                    <textarea
                      id="cal_caption"
                      rows={3}
                      value={form.caption}
                      onChange={(event) => setForm((current) => ({ ...current, caption: event.target.value }))}
                    />
                  </div>
                  <button type="submit" className="btn" disabled={saving}>
                    {saving ? "Saving..." : "Schedule item"}
                  </button>
                </form>
              </section>
            </>
          )}
        </>
      ) : null}
    </section>
  );
}
