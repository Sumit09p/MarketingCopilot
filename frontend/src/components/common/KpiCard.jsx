export default function KpiCard({ label, value, hint }) {
  return (
    <article className="kpi-card">
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>
      {hint ? <p className="kpi-hint muted">{hint}</p> : null}
    </article>
  );
}
