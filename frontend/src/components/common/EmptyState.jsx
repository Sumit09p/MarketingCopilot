export default function EmptyState({ title, description, action = null }) {
  return (
    <div className="state-block empty-state">
      {title ? <h2>{title}</h2> : null}
      {description ? <p className="muted">{description}</p> : null}
      {action}
    </div>
  );
}
