import { Link } from "react-router-dom";
import StatusBadge from "../common/StatusBadge";
import { formatCurrency, formatDate, formatList } from "../../utils/format";

export default function CampaignCard({ campaign }) {
  return (
    <article className="entity-card">
      <div className="entity-card-head">
        <h2>{campaign.name || "Untitled campaign"}</h2>
        <StatusBadge status={campaign.status} />
      </div>
      <dl className="meta-list">
        {campaign.objective ? (
          <>
            <dt>Objective</dt>
            <dd>{campaign.objective}</dd>
          </>
        ) : null}
        {campaign.product ? (
          <>
            <dt>Product</dt>
            <dd>{campaign.product}</dd>
          </>
        ) : null}
        {campaign.audience ? (
          <>
            <dt>Audience</dt>
            <dd>{campaign.audience}</dd>
          </>
        ) : null}
        {campaign.platforms ? (
          <>
            <dt>Platforms</dt>
            <dd>{formatList(campaign.platforms)}</dd>
          </>
        ) : null}
        {campaign.budget !== undefined && campaign.budget !== null ? (
          <>
            <dt>Budget</dt>
            <dd>{formatCurrency(campaign.budget)}</dd>
          </>
        ) : null}
        {campaign.duration?.start || campaign.duration?.end ? (
          <>
            <dt>Duration</dt>
            <dd>
              {formatDate(campaign.duration?.start)} – {formatDate(campaign.duration?.end)}
            </dd>
          </>
        ) : null}
      </dl>
      <div className="entity-card-actions">
        <Link className="btn" to={`/campaigns/${campaign.id}`}>
          Open campaign
        </Link>
      </div>
    </article>
  );
}
