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
const MONTHS = Array.from({ length: 12 }, (_, index) => new Date(2000, index, 1).toLocaleString(undefined, { month: "long" }));

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
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState(null);
  const [editError, setEditError] = useState("");
  const [editSuccess, setEditSuccess] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

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
  const yearOptions = Array.from({ length: 21 }, (_, index) => year - 10 + index);

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
  function startEditing(entry) {
    setEditingId(entry.id);
    setEditDraft({
      date: entry.date || "",
      campaignId,
      type: entry.type || TYPES[0],
      platform: entry.platform || PLATFORMS[0],
      status: entry.status || STATUSES[0],
      caption: entry.caption || "",
    });
    setEditError("");
    setEditSuccess("");
  }

  function cancelEditing() {
    setEditingId(null);
    setEditDraft(null);
    setEditError("");
  }

  async function saveEdit(entry) {
    setEditError("");
    setEditSuccess("");
    if (!editDraft?.date || !editDraft.platform || !editDraft.type || !editDraft.status) {
      setEditError("Date, campaign, type, platform, and status are required.");
      return;
    }
    setSavingEdit(true);
    try {
      const updated = await calendarService.updateCalendarItem(campaignId, entry.id, {
        ...editDraft,
        caption: editDraft.caption.trim(),
      });
      if (!updated || typeof updated !== "object" || !updated.id) {
        throw new Error("The calendar service did not return the updated item.");
      }
      if (editDraft.campaignId !== campaignId) {
        setEntries((current) => current.filter((item) => item.id !== entry.id));
      } else {
        setEntries((current) => current.map((item) => item.id === entry.id ? updated : item));
      }
      setEditingId(null);
      setEditDraft(null);
      setEditSuccess("Calendar item updated.");
    } catch (err) {
      setEditError(getUserFacingError(err, "Could not update that calendar item."));
    } finally {
      setSavingEdit(false);
    }
  }

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
                      cancelEditing();
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
                <div className="month-nav" aria-label="Calendar month and year">
                  <label className="form-field compact">
                    <span>Month</span>
                    <select aria-label="Calendar month" value={monthIndex} onChange={(event) => setCursor(new Date(year, Number(event.target.value), 1))}>
                      {MONTHS.map((month, index) => <option key={month} value={index}>{month}</option>)}
                    </select>
                  </label>
                  <label className="form-field compact">
                    <span>Year</span>
                    <select aria-label="Calendar year" value={year} onChange={(event) => setCursor(new Date(Number(event.target.value), monthIndex, 1))}>
                      {yearOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                    </select>
                  </label>
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
                {editError ? <p className="error-text" role="alert">{editError}</p> : null}
                {editSuccess ? <p className="success-text" role="status">{editSuccess}</p> : null}
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
                          <th><span className="visually-hidden">Actions</span></th>
                        </tr>
                      </thead>
                      <tbody>
                        {entries.map((entry) => {
                          const isEditing = editingId === entry.id;
                          const field = (name, label, value, options) => options ? (
                            <select className="schedule-edit-field" aria-label={label} value={value} onChange={(event) => setEditDraft((current) => ({ ...current, [name]: event.target.value }))}>
                              {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                            </select>
                          ) : <input className="schedule-edit-field" aria-label={label} type={name === "date" ? "date" : "text"} value={value} onChange={(event) => setEditDraft((current) => ({ ...current, [name]: event.target.value }))} />;
                          return (
                            <tr key={entry.id}>
                              <td>{isEditing ? field("date", "Schedule date", editDraft.date) : formatDate(entry.date)}</td>
                              <td>{isEditing ? field("campaignId", "Campaign", editDraft.campaignId, campaigns.map((item) => ({ value: item.id, label: item.name }))) : selectedCampaign?.name || campaignId}</td>
                              <td>{isEditing ? field("type", "Content type", editDraft.type, TYPES.map((item) => ({ value: item, label: item }))) : entry.type}</td>
                              <td>{isEditing ? field("platform", "Platform", editDraft.platform, PLATFORMS.map((item) => ({ value: item, label: item }))) : entry.platform}</td>
                              <td>{isEditing ? field("status", "Status", editDraft.status, STATUSES.map((item) => ({ value: item, label: item }))) : <StatusBadge status={entry.status} />}</td>
                              <td>{isEditing ? <textarea className="schedule-edit-caption" aria-label="Caption" rows={2} value={editDraft.caption} onChange={(event) => setEditDraft((current) => ({ ...current, caption: event.target.value }))} /> : entry.caption || "-"}</td>
                              <td className="schedule-row-action">
                                {isEditing ? <div className="schedule-edit-actions">
                                  <button type="button" className="icon-button" onClick={() => saveEdit(entry)} disabled={savingEdit} aria-label="Save schedule changes" title="Save changes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12.5 9.5 17 19 7.5" /></svg></button>
                                  <button type="button" className="icon-button schedule-cancel-edit" onClick={cancelEditing} disabled={savingEdit} aria-label="Cancel schedule edit" title="Cancel"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg></button>
                                </div> : <button type="button" className="icon-button" onClick={() => startEditing(entry)} disabled={Boolean(editingId)} aria-label={`Edit ${entry.caption || "schedule item"}`} title="Edit schedule item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m15 5 4 4M4 20l4-.8L19 8a2.1 2.1 0 0 0-3-3L5 16l-1 4Z" /></svg></button>}
                              </td>
                            </tr>
                          );
                        })}
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
