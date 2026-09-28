import { useCallback, useEffect, useState } from "react";
import DemoBanner from "../components/common/DemoBanner";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import { isMockApiEnabled, integrationsService } from "../services";
import { getUserFacingError } from "../utils/errors";
import { formatProviderName } from "../utils/format";

function redirectUrlFrom(data) {
  if (!data || typeof data !== "object") return "";
  const candidates = [data.authorization_url, data.redirect_url, data.auth_url, data.url];
  const found = candidates.find((value) => typeof value === "string" && value.trim());
  return found ? found.trim() : "";
}

export default function IntegrationsPage() {
  const [status, setStatus] = useState("loading");
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionNote, setActionNote] = useState("");
  const [connecting, setConnecting] = useState("");

  const loadIntegrations = useCallback(async () => {
    setStatus("loading");
    setError("");
    try {
      const data = await integrationsService.listIntegrations();
      setItems(Array.isArray(data) ? data : []);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load integrations."));
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    loadIntegrations();
  }, [loadIntegrations]);

  async function onConnect(provider) {
    if (!provider) return;
    setConnecting(provider);
    setActionError("");
    setActionNote("");
    try {
      const result = await integrationsService.connectIntegration(provider);
      const redirect = redirectUrlFrom(result);
      if (redirect) {
        window.location.assign(redirect);
        return;
      }
      await loadIntegrations();
      const nextStatus = result?.status ? String(result.status).toUpperCase() : "";
      if (nextStatus === "CONNECTED") {
        setActionNote(`${formatProviderName(provider)} is connected.`);
      } else if (nextStatus === "COMING_SOON") {
        setActionNote(`${formatProviderName(provider)} is not available yet.`);
      } else {
        setActionNote(
          `Connect was requested for ${formatProviderName(provider)}. Authorization stays on the backend; no third-party passwords are collected here.`
        );
      }
    } catch (err) {
      setActionError(getUserFacingError(err, "Could not start that integration connection."));
    } finally {
      setConnecting("");
    }
  }

  return (
    <section className="page-stack">
      <PageHeader
        title="Integrations"
        description="Connect official marketing data sources. OAuth and API credentials are handled by the backend. This app never asks for third-party passwords or secrets."
        actions={
          <button type="button" className="btn btn-secondary" onClick={loadIntegrations} disabled={status === "loading"}>
            Refresh
          </button>
        }
      />

      {isMockApiEnabled ? (
        <DemoBanner text="Demo integrations — mock connection states, not live OAuth." />
      ) : null}

      {status === "loading" ? <LoadingState message="Loading integrations..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={loadIntegrations} /> : null}

      {status === "ready" && items.length === 0 ? (
        <div className="page-card">
          <EmptyState
            title="No integrations available"
            description="The integrations API did not return any providers."
          />
        </div>
      ) : null}

      {status === "ready" && items.length > 0 ? (
        <>
          {actionError ? <p className="error-text">{actionError}</p> : null}
          {actionNote ? <p className="success-text">{actionNote}</p> : null}
          <div className="card-grid">
            {items.map((item) => {
              const provider = item.provider;
              const connection = String(item.status || "NOT_CONNECTED").toUpperCase();
              const comingSoon = connection === "COMING_SOON";
              const connected = connection === "CONNECTED";
              const canConnect = !comingSoon && !connected;
              return (
                <article key={provider} className="entity-card">
                  <div className="entity-card-head">
                    <h2>{formatProviderName(provider)}</h2>
                    <StatusBadge status={connection} />
                  </div>
                  {item.description ? <p className="muted">{item.description}</p> : null}
                  {item.category ? (
                    <dl className="meta-list">
                      <dt>Category</dt>
                      <dd>{item.category}</dd>
                    </dl>
                  ) : (
                    <p className="muted">
                      {comingSoon
                        ? "This provider is listed as coming soon and cannot be connected yet."
                        : connected
                          ? "Connected. Disconnect is not available in the current API contract."
                          : "Connect starts the backend-controlled authorization flow for this provider."}
                    </p>
                  )}
                  <div className="entity-card-actions">
                    {canConnect ? (
                      <button
                        type="button"
                        className="btn"
                        disabled={Boolean(connecting)}
                        onClick={() => onConnect(provider)}
                      >
                        {connecting === provider ? "Connecting..." : "Connect"}
                      </button>
                    ) : null}
                    {comingSoon ? (
                      <button type="button" className="btn" disabled>
                        Coming soon
                      </button>
                    ) : null}
                    {connected ? (
                      <button type="button" className="btn btn-secondary" disabled>
                        Connected
                      </button>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>
        </>
      ) : null}
    </section>
  );
}
