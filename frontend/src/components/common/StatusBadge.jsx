const TONE = {
  ACTIVE: "ok",
  COMPLETED: "ok",
  SCHEDULED: "ok",
  READY: "ok",
  CONNECTED: "ok",
  RUNNING: "info",
  STARTED: "info",
  PROCESSING: "info",
  PENDING: "neutral",
  DRAFT: "neutral",
  COMING_SOON: "neutral",
  NOT_CONNECTED: "warn",
  BLOCKED: "warn",
  FAILED: "bad",
  ERROR: "bad",
};

export default function StatusBadge({ status }) {
  if (!status) return <span className="status-badge tone-neutral">Unknown</span>;
  const key = String(status).toUpperCase();
  const tone = TONE[key] || "neutral";
  const label = key.replace(/_/g, " ");
  return <span className={`status-badge tone-${tone}`}>{label}</span>;
}
