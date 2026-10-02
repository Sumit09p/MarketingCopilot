import { useState } from "react";
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
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

export default function CampaignWorkspace({ campaign }) {
  const [activeTab, setActiveTab] = useState("overview");
  const tabs = [
    { id: "overview", label: "Overview", title: "Campaign overview", hasData: !isBlank(campaign), empty: "Campaign details are not available yet.", content: <dl className="meta-list"><dt>Name</dt><dd>{campaign.name || "—"}</dd><dt>Objective</dt><dd>{campaign.objective || "—"}</dd><dt>Product</dt><dd>{campaign.product || "—"}</dd><dt>Audience</dt><dd>{campaign.audience || "—"}</dd><dt>Platforms</dt><dd>{Array.isArray(campaign.platforms) && campaign.platforms.length ? campaign.platforms.join(", ") : "—"}</dd><dt>Budget</dt><dd>{campaign.budget ?? "—"}</dd><dt>Status</dt><dd>{campaign.status || "—"}</dd></dl> },
    { id: "research", label: "Research", title: "Research", hasData: !isBlank(campaign.research), empty: "Research results are not available yet.", content: <JsonBlock value={campaign.research} /> },
    { id: "competitor", label: "Competitor Analysis", title: "Competitor analysis", hasData: !isBlank(campaign.competitor_analysis), empty: "Competitor analysis is not available yet.", content: <JsonBlock value={campaign.competitor_analysis} /> },
    { id: "seo", label: "SEO", title: "SEO", hasData: !isBlank(campaign.seo), empty: "SEO results are not available yet.", content: <JsonBlock value={campaign.seo} /> },
    { id: "content", label: "Content", title: "Content", hasData: !isBlank(campaign.content), empty: "Content is not available yet.", content: <JsonBlock value={campaign.content} /> },
    { id: "creatives", label: "Creatives", title: "Creatives", hasData: Array.isArray(campaign.creatives) && campaign.creatives.length > 0, empty: "Creatives are not available yet.", content: <JsonBlock value={campaign.creatives} /> },
    { id: "calendar", label: "Calendar", title: "Calendar", hasData: Array.isArray(campaign.calendar) && campaign.calendar.length > 0, empty: "Calendar entries are not available yet.", content: <JsonBlock value={campaign.calendar} /> },
    { id: "analytics", label: "Analytics", title: "Analytics", hasData: !isBlank(campaign.analytics), empty: "Analytics for this campaign are not available yet.", content: <JsonBlock value={campaign.analytics} /> },
  ];
  const selected = tabs.find((tab) => tab.id === activeTab) || tabs[0];

  return (
    <div className="campaign-workspace">
      <div className="workspace-tabs" role="tablist" aria-label="Campaign workspace sections">
        {tabs.map((tab) => (
          <button key={tab.id} id={`campaign-tab-${tab.id}`} type="button" role="tab" aria-selected={activeTab === tab.id} aria-controls="campaign-workspace-panel" tabIndex={0} className={`workspace-tab${activeTab === tab.id ? " active" : ""}`} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>
      <div id="campaign-workspace-panel" className="workspace-grid" role="tabpanel" aria-labelledby={`campaign-tab-${selected.id}`} tabIndex={0}>
        <Section title={selected.title} hasData={selected.hasData} emptyMessage={selected.empty}>{selected.content}</Section>
      </div>
    </div>
  );
}
