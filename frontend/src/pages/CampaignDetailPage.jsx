import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import CampaignWorkspace from "../components/campaigns/CampaignWorkspace";
import WorkflowPanel, { isRunActive } from "../components/campaigns/WorkflowPanel";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import { agentRunsService, campaignsService } from "../services";
import { getUserFacingError } from "../utils/errors";

const POLL_MS = 2500;

export default function CampaignDetailPage() {
  const { campaignId } = useParams();
  const [status, setStatus] = useState("loading");
  const [campaign, setCampaign] = useState(null);
  const [error, setError] = useState("");
  const [instruction, setInstruction] = useState("Create the complete marketing plan");
  const [runId, setRunId] = useState(null);
  const [run, setRun] = useState(null);
  const [agentDetail, setAgentDetail] = useState(null);
  const [starting, setStarting] = useState(false);
  const [runError, setRunError] = useState("");
  const pollRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  async function loadCampaign() {
    setStatus("loading");
    setError("");
    try {
      const data = await campaignsService.getCampaign(campaignId);
      if (!data) {
        setCampaign(null);
        setError("This campaign was not found.");
        setStatus("error");
        return;
      }
      setCampaign(data);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load this campaign."));
      setStatus("error");
    }
  }

  useEffect(() => {
    loadCampaign();
  }, [campaignId]);

  const fetchRun = useCallback(
    async (id) => {
      const data = await campaignsService.getCampaignRun(campaignId, id);
      if (!data) {
        setRun(null);
        setAgentDetail(null);
        return null;
      }
      setRun(data);
      try {
        const detail = await agentRunsService.getAgentRun(id);
        setAgentDetail(detail);
      } catch {
        setAgentDetail(null);
      }
      return data;
    },
    [campaignId]
  );

  useEffect(() => {
    stopPolling();
    if (!runId) return undefined;

    let cancelled = false;

    async function tick() {
      try {
        const data = await fetchRun(runId);
        if (cancelled) return;
        if (String(data?.status).toUpperCase() === "COMPLETED") {
          try {
            const latestCampaign = await campaignsService.getCampaign(campaignId);
            if (!cancelled && latestCampaign) setCampaign(latestCampaign);
          } catch {
            // Keep the run result visible if the campaign refresh is temporarily unavailable.
          }
        }
        if (!data || !isRunActive(data?.status)) stopPolling();
      } catch (err) {
        if (cancelled) return;
        setRunError(getUserFacingError(err, "Could not refresh run status."));
        stopPolling();
      }
    }

    tick();
    pollRef.current = window.setInterval(tick, POLL_MS);

    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [runId, fetchRun, stopPolling]);

  async function handleRun() {
    setStarting(true);
    setRunError("");
    try {
      const started = await campaignsService.runCampaign(campaignId, {
        instruction: instruction.trim() || "Create the complete marketing plan",
      });
      setRunId(started.run_id);
      setRun({ run_id: started.run_id, status: started.status, tasks: [] });
    } catch (err) {
      setRunError(getUserFacingError(err, "Could not start the campaign run."));
    } finally {
      setStarting(false);
    }
  }

  return (
    <section className="page-stack">
      <PageHeader
        title={campaign?.name || "Campaign workspace"}
        description="Campaign lifecycle, workspace sections, and orchestrated agent runs."
        badge={campaign?.status ? <StatusBadge status={campaign.status} /> : null}
        actions={
          <Link className="btn btn-secondary" to="/campaigns">
            All campaigns
          </Link>
        }
      />

      {status === "loading" ? <LoadingState message="Loading campaign workspace..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={loadCampaign} /> : null}

      {status === "ready" && campaign ? (
        <>
          <WorkflowPanel
            run={run}
            agentDetail={agentDetail}
            instruction={instruction}
            onInstructionChange={setInstruction}
            onRun={handleRun}
            running={starting}
            runError={runError}
          />
          <CampaignWorkspace campaign={campaign} />
        </>
      ) : null}
    </section>
  );
}
