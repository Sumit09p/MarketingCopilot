import { useEffect, useState } from "react";
import DemoBanner from "../components/common/DemoBanner";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import KpiCard from "../components/common/KpiCard";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import TimeseriesChart from "../components/common/TimeseriesChart";
import { analyticsService, campaignsService, isMockApiEnabled } from "../services";
import { getUserFacingError } from "../utils/errors";
import { formatNumber, formatPercent } from "../utils/format";

export default function AnalyticsPage() {
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [series, setSeries] = useState([]);
  const [insights, setInsights] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [campaignId, setCampaignId] = useState("");
  const [metric, setMetric] = useState("traffic");
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState("");

  async function loadAnalytics(selectedCampaignId = campaignId) {
    setStatus("loading");
    setError("");
    try {
      const params = selectedCampaignId ? { campaign_id: selectedCampaignId } : {};
      const [summaryData, seriesData, campaignData] = await Promise.all([
        analyticsService.getSummary(),
        analyticsService.getTimeseries(params),
        campaignsService.listCampaigns(),
      ]);
      setSummary(summaryData);
      setSeries(Array.isArray(seriesData) ? seriesData : []);
      setCampaigns(Array.isArray(campaignData) ? campaignData : []);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load analytics."));
      setStatus("error");
    }
  }

  useEffect(() => {
    loadAnalytics("");
  }, []);

  async function loadInsights() {
    setInsightsLoading(true);
    setInsightsError("");
    try {
      const selected = campaignId || campaigns[0]?.id;
      if (!selected) {
        setInsightsError("Select a campaign to load insights.");
        setInsightsLoading(false);
        return;
      }
      const data = await analyticsService.getInsights({ campaign_id: selected });
      setInsights(data);
    } catch (err) {
      setInsightsError(getUserFacingError(err, "Could not load insights."));
    } finally {
      setInsightsLoading(false);
    }
  }

  const sample = Boolean(summary?.is_sample_data) || isMockApiEnabled;

  return (
    <section className="page-stack">
      <PageHeader
        title="Analytics"
        description="Summary, time series, and insights from the analytics API. Only documented metrics are shown."
      />

      {status === "loading" ? <LoadingState message="Loading analytics..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={() => loadAnalytics(campaignId)} /> : null}

      {status === "ready" ? (
        <>
          <DemoBanner sample={sample} />

          <div className="filter-bar">
            <label className="form-field compact" htmlFor="analytics-campaign">
              Campaign filter
              <select
                id="analytics-campaign"
                value={campaignId}
                onChange={(event) => {
                  const next = event.target.value;
                  setCampaignId(next);
                  loadAnalytics(next);
                }}
              >
                <option value="">All campaigns</option>
                {campaigns.map((campaign) => (
                  <option key={campaign.id} value={campaign.id}>
                    {campaign.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field compact" htmlFor="analytics-metric">
              Chart metric
              <select id="analytics-metric" value={metric} onChange={(event) => setMetric(event.target.value)}>
                <option value="traffic">Traffic</option>
                <option value="engagement">Engagement</option>
                <option value="conversions">Conversions</option>
              </select>
            </label>
          </div>

          {summary ? (
            <div className="kpi-grid">
              <KpiCard label="Traffic" value={formatNumber(summary.traffic)} />
              <KpiCard label="Engagement" value={formatNumber(summary.engagement)} />
              <KpiCard label="Conversions" value={formatNumber(summary.conversions)} />
              <KpiCard label="Revenue" value={formatNumber(summary.revenue)} />
              <KpiCard label="CTR" value={formatPercent(summary.ctr)} />
              <KpiCard label="Conversion rate" value={formatPercent(summary.conversion_rate)} />
              <KpiCard label="ROI" value={summary.roi ?? "—"} />
            </div>
          ) : (
            <EmptyState title="No summary" description="The analytics summary API did not return metrics." />
          )}

          <section className="page-card">
            <h2>Time series</h2>
            {series.length === 0 ? (
              <EmptyState title="No time-series data" description="No points were returned for the selected filter." />
            ) : (
              <TimeseriesChart points={series} metric={metric} />
            )}
          </section>

          <section className="page-card">
            <div className="page-header">
              <h2>Insights</h2>
              <button type="button" className="btn" onClick={loadInsights} disabled={insightsLoading}>
                {insightsLoading ? "Loading insights..." : "Load insights"}
              </button>
            </div>
            {insightsError ? <p className="error-text">{insightsError}</p> : null}
            {!insights && !insightsLoading ? (
              <p className="muted">Insights are requested from POST /api/analytics/insights when you load them.</p>
            ) : null}
            {insights ? (
              <div>
                <p>{insights.summary || "No summary was returned."}</p>
                <h3 className="section-title">Observations</h3>
                {Array.isArray(insights.observations) && insights.observations.length > 0 ? (
                  <ul className="plain-list">
                    {insights.observations.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No observations were returned.</p>
                )}
                <h3 className="section-title">Recommendations</h3>
                {Array.isArray(insights.recommendations) && insights.recommendations.length > 0 ? (
                  <ul className="plain-list">
                    {insights.recommendations.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No recommendations were returned.</p>
                )}
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </section>
  );
}
