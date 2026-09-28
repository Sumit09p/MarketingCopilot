import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DemoBanner from "../components/common/DemoBanner";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import KpiCard from "../components/common/KpiCard";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import { analyticsService, campaignsService, isMockApiEnabled } from "../services";
import { getUserFacingError } from "../utils/errors";
import { formatNumber, formatPercent } from "../utils/format";

export default function DashboardPage() {
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [campaigns, setCampaigns] = useState([]);

  async function loadDashboard() {
    setStatus("loading");
    setError("");
    try {
      const [summaryData, campaignData] = await Promise.all([
        analyticsService.getSummary(),
        campaignsService.listCampaigns(),
      ]);
      setSummary(summaryData);
      setCampaigns(Array.isArray(campaignData) ? campaignData : []);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load the dashboard."));
      setStatus("error");
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const sample = Boolean(summary?.is_sample_data) || isMockApiEnabled;
  const recent = campaigns.slice(0, 5);
  const active = campaigns.filter((item) => String(item.status).toUpperCase() === "ACTIVE");

  return (
    <section className="page-stack">
      <PageHeader
        title="Dashboard"
        description="Campaign counts and analytics summary from the existing APIs."
        actions={
          <Link className="btn" to="/campaigns/new">
            Create Campaign
          </Link>
        }
      />

      {status === "loading" ? <LoadingState message="Loading dashboard..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={loadDashboard} /> : null}

      {status === "ready" ? (
        <>
          <DemoBanner sample={sample} />

          <div className="kpi-grid">
            <KpiCard label="Campaigns (analytics)" value={formatNumber(summary?.campaigns)} />
            <KpiCard label="Campaigns listed" value={formatNumber(campaigns.length)} />
            <KpiCard label="Active campaigns" value={formatNumber(active.length)} />
            <KpiCard label="Traffic" value={formatNumber(summary?.traffic)} />
            <KpiCard label="Engagement" value={formatNumber(summary?.engagement)} />
            <KpiCard label="Conversions" value={formatNumber(summary?.conversions)} />
            <KpiCard label="Revenue" value={formatNumber(summary?.revenue)} />
            <KpiCard label="CTR" value={formatPercent(summary?.ctr)} />
            <KpiCard label="Conversion rate" value={formatPercent(summary?.conversion_rate)} />
            <KpiCard label="ROI" value={summary?.roi ?? "—"} />
          </div>

          <div className="split-grid">
            <section className="page-card">
              <h2>Recent campaigns</h2>
              {recent.length === 0 ? (
                <EmptyState title="No campaigns" description="Create a campaign to see it here." />
              ) : (
                <ul className="plain-list activity-list">
                  {recent.map((campaign) => (
                    <li key={campaign.id}>
                      <Link to={`/campaigns/${campaign.id}`}>{campaign.name}</Link>
                      <StatusBadge status={campaign.status} />
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="page-card">
              <h2>Quick actions</h2>
              <div className="quick-actions">
                <Link className="btn" to="/campaigns/new">
                  New campaign
                </Link>
                <Link className="btn btn-secondary" to="/brand">
                  Brand profile
                </Link>
                <Link className="btn btn-secondary" to="/analytics">
                  Analytics
                </Link>
                <Link className="btn btn-secondary" to="/calendar">
                  Calendar
                </Link>
                <Link className="btn btn-secondary" to="/chat">
                  Chat
                </Link>
                <Link className="btn btn-secondary" to="/knowledge">
                  Knowledge
                </Link>
                <Link className="btn btn-secondary" to="/integrations">
                  Integrations
                </Link>
              </div>
            </section>
          </div>
        </>
      ) : null}
    </section>
  );
}
