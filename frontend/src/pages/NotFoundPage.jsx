import { Link } from "react-router-dom";
import EmptyState from "../components/common/EmptyState";
import PageHeader from "../components/common/PageHeader";

export default function NotFoundPage() {
  return (
    <section className="page-stack">
      <PageHeader title="Page not found" description="That URL is not part of the MarketingOS workspace." />
      <div className="page-card">
        <EmptyState
          title="Nothing here"
          description="Check the sidebar or go back to Chat."
          action={
            <Link className="btn" to="/chat">
              Back to Chat
            </Link>
          }
        />
      </div>
    </section>
  );
}
