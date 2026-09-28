import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import CampaignCard from "../components/campaigns/CampaignCard";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import { campaignsService } from "../services";
import { getUserFacingError } from "../utils/errors";

export default function CampaignsPage() {
  const [status, setStatus] = useState("loading");
  const [campaigns, setCampaigns] = useState([]);
  const [error, setError] = useState("");

  async function loadCampaigns() {
    setStatus("loading");
    setError("");
    try {
      const data = await campaignsService.listCampaigns();
      setCampaigns(Array.isArray(data) ? data : []);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load campaigns."));
      setStatus("error");
    }
  }

  useEffect(() => {
    loadCampaigns();
  }, []);

  return (
    <section className="page-stack">
      <PageHeader
        title="Campaigns"
        description="Create and open campaign workspaces. Only campaigns returned by the API are shown."
        actions={
          <>
            <button type="button" className="btn btn-secondary" onClick={loadCampaigns}>
              Refresh
            </button>
            <Link className="btn" to="/campaigns/new">
              Create Campaign
            </Link>
          </>
        }
      />

      {status === "loading" ? <LoadingState message="Loading campaigns..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={loadCampaigns} /> : null}

      {status === "ready" && campaigns.length === 0 ? (
        <div className="page-card">
          <EmptyState
            title="No campaigns yet"
            description="Create a campaign to start a workspace. Nothing is invented here — the list stays empty until the API returns campaigns."
            action={
              <Link className="btn" to="/campaigns/new">
                Create Campaign
              </Link>
            }
          />
        </div>
      ) : null}

      {status === "ready" && campaigns.length > 0 ? (
        <div className="card-grid">
          {campaigns.map((campaign) => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
