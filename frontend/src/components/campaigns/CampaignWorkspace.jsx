import { isBlank } from "../../utils/format";

function Section({ title, emptyMessage, children, hasData }) {
  return (
    <section className="workspace-section">
      <h2>{title}</h2>
      {hasData ? children : <p className="muted">{emptyMessage}</p>}
    </section>
  );
}

function JsonBlock({ value }) {
  if (typeof value === "string") return <p>{value}</p>;
  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    return (
      <ul className="plain-list">
        {value.map((item, index) => (
          <li key={index}>{typeof item === "string" ? item : JSON.stringify(item)}</li>
        ))}
      </ul>
    );
  }
  return (
    <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>
  );
}

export default function CampaignWorkspace({ campaign }) {
  return (
    <div className="workspace-grid">
      <Section title="Campaign overview" hasData={!isBlank(campaign)} emptyMessage="Campaign details are not available yet.">
        <dl className="meta-list">
          <dt>Name</dt>
          <dd>{campaign.name || "—"}</dd>
          <dt>Objective</dt>
          <dd>{campaign.objective || "—"}</dd>
          <dt>Product</dt>
          <dd>{campaign.product || "—"}</dd>
          <dt>Audience</dt>
          <dd>{campaign.audience || "—"}</dd>
          <dt>Platforms</dt>
          <dd>{Array.isArray(campaign.platforms) && campaign.platforms.length ? campaign.platforms.join(", ") : "—"}</dd>
          <dt>Budget</dt>
          <dd>{campaign.budget ?? "—"}</dd>
          <dt>Status</dt>
          <dd>{campaign.status || "—"}</dd>
        </dl>
      </Section>

      <Section title="Research" hasData={!isBlank(campaign.research)} emptyMessage="Research results are not available yet.">
        <JsonBlock value={campaign.research} />
      </Section>
      <Section
        title="Competitor analysis"
        hasData={!isBlank(campaign.competitor_analysis)}
        emptyMessage="Competitor analysis is not available yet."
      >
        <JsonBlock value={campaign.competitor_analysis} />
      </Section>
      <Section title="SEO" hasData={!isBlank(campaign.seo)} emptyMessage="SEO results are not available yet.">
        <JsonBlock value={campaign.seo} />
      </Section>
      <Section title="Content" hasData={!isBlank(campaign.content)} emptyMessage="Content is not available yet.">
        <JsonBlock value={campaign.content} />
      </Section>
      <Section
        title="Creatives"
        hasData={Array.isArray(campaign.creatives) && campaign.creatives.length > 0}
        emptyMessage="Creatives are not available yet."
      >
        <JsonBlock value={campaign.creatives} />
      </Section>
      <Section
        title="Calendar"
        hasData={Array.isArray(campaign.calendar) && campaign.calendar.length > 0}
        emptyMessage="Calendar entries are not available yet."
      >
        <JsonBlock value={campaign.calendar} />
      </Section>
      <Section title="Analytics" hasData={!isBlank(campaign.analytics)} emptyMessage="Analytics for this campaign are not available yet.">
        <JsonBlock value={campaign.analytics} />
      </Section>
    </div>
  );
}
