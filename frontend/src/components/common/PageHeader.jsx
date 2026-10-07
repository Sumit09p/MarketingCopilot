export default function PageHeader({ title, description, actions = null, badge = null }) {
  return (
    <div className="page-header">
      <div>
        <div className="page-header-title-row">
          <h1>{title}</h1>
          {badge}
        </div>
        {description ? <p className="muted">{description}</p> : null}
      </div>
      {actions ? <div className="page-header-actions">{actions}</div> : null}
    </div>
  );
}
