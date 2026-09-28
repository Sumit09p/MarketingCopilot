const TONE = {
  ACTIVE: "ok",
  COMPLETED: "ok",
  SCHEDULED: "ok",
  RUNNING: "info",
  STARTED: "info",
  PENDING: "neutral",
  DRAFT: "neutral",
  BLOCKED: "warn",
  FAILED: "bad",
};

export default function StatusBadge({ status }) {
  if (!status) return <span className="status-badge tone-neutral">Unknown</span>;
  const key = String(status).toUpperCase();
  const tone = TONE[key] || "neutral";
  return <span className={`status-badge tone-${tone}`}>{key}</span>;
}
