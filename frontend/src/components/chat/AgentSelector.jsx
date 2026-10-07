import { AGENTS } from "../../utils/constants";

export default function AgentSelector({ value, onChange, disabled }) {
  return (
    <label className={`agent-selector agent-${value || "auto"}`}>
      Agent
      <select
        className="agent-select"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label="Agent selector"
        disabled={disabled}
      >
        <option value="">Auto / General</option>
        {AGENTS.map((agent) => (
          <option key={agent} value={agent}>
            {agent}
          </option>
        ))}
      </select>
    </label>
  );
}
