import { isMockApiEnabled } from "../../services";

export default function DemoBanner({ sample = false, text }) {
  if (!isMockApiEnabled && !sample) return null;
  return (
    <p className="demo-banner" role="note">
      {text || "Demo data — sample metrics for UI development, not live business performance."}
    </p>
  );
}
