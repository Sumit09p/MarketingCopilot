import { Link } from "react-router-dom";
import PagePlaceholder from "../components/common/PagePlaceholder";

export default function CampaignsPage() {
  return (
    <section>
      <PagePlaceholder
        title="Campaigns"
        description="Placeholder page. Campaign list and workflow visualization will be added later."
      />
      <p style={{ marginTop: 16 }}>
        <Link className="btn" to="/campaigns/new">
          New campaign
        </Link>
      </p>
    </section>
  );
}
