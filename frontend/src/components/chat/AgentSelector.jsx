import { AGENTS } from "../../utils/constants";

export default function AgentSelector() {
  return (
    <label>
      Agent
      <select className="agent-select" defaultValue="" aria-label="Agent selector">
        <option value="">General</option>
        {AGENTS.map((agent) => (
          <option key={agent} value={agent}>
            {agent}
          </option>
        ))}
      </select>
    </label>
  );
}
