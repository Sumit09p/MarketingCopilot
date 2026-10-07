import StatusBadge from "../common/StatusBadge";
import { formatDateTime } from "../../utils/format";

const STAGE_ORDER = [
  { id: "planning", label: "Planning", agents: [] },
  { id: "research", label: "Research", agents: ["research", "competitor"] },
  { id: "production", label: "Content / SEO / Creative", agents: ["seo", "content", "image"] },
  { id: "analysis", label: "Analysis", agents: ["analytics"] },
  { id: "recommendations", label: "Recommendations", agents: [] },
];

const ACTIVE_STATUSES = new Set(["PENDING", "RUNNING", "STARTED"]);
const STOP_STATUSES = new Set(["COMPLETED", "FAILED", "BLOCKED"]);

export function isRunActive(status) {
  const key = String(status || "").toUpperCase();
  return ACTIVE_STATUSES.has(key) && !STOP_STATUSES.has(key);
}

function progressFromTasks(tasks) {
  if (!tasks.length) return 0;
  const done = tasks.filter((task) => String(task.status).toUpperCase() === "COMPLETED").length;
  return Math.round((done / tasks.length) * 100);
}

export default function WorkflowPanel({
  run,
  agentDetail,
  instruction,
  onInstructionChange,
  onRun,
  running,
  runError,
}) {
  const tasks = Array.isArray(run?.tasks) ? run.tasks : [];
  const progress = progressFromTasks(tasks);
  const overall = run?.status || (running ? "STARTING" : null);

  return (
    <section className="page-card workflow-card">
      <div className="page-header">
        <div>
          <h2>Campaign run</h2>
          <p className="muted">The backend planner and orchestrator execute agents. This view only reports returned status.</p>
        </div>
        {overall ? <StatusBadge status={overall} /> : null}
      </div>

      <div className="form-field">
        <label htmlFor="run_instruction">Instruction</label>
        <input
          id="run_instruction"
          value={instruction}
          onChange={(event) => onInstructionChange(event.target.value)}
          placeholder="Create the complete marketing plan"
        />
      </div>

      <div className="form-actions">
        <button type="button" className="btn" onClick={onRun} disabled={running}>
          {running ? "Starting run..." : "Run Campaign"}
        </button>
      </div>
      {runError ? <p className="error-text">{runError}</p> : null}

      {!run && !running ? (
        <p className="muted">No workflow run yet. Start a run to see task status from the API.</p>
      ) : null}

      {run ? (
        <>
          <div className="progress-block">
            <div className="progress-label">
              Progress based on returned task states: {progress}%
            </div>
            <div className="progress-track" aria-hidden="true">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>

          <ol className="workflow-stages">
            {STAGE_ORDER.map((stage) => {
              const assignedAgents = STAGE_ORDER.flatMap((item) => item.agents);
              const stageTasks =
                stage.id === "planning"
                  ? tasks.filter((task) => !assignedAgents.includes(task.agent))
                  : tasks.filter((task) => stage.agents.includes(task.agent));
              return (
                <li key={stage.id} className="workflow-stage">
                  <h3>{stage.label}</h3>
                  {stage.id === "recommendations" ? (
                    <p className="muted">Recommendations appear in agent-run results when the API returns them.</p>
                  ) : null}
                  {stageTasks.length === 0 && stage.id !== "recommendations" ? (
                    <p className="muted">
                      {stage.id === "planning"
                        ? "Planning is owned by the backend orchestrator. No extra planning tasks were returned."
                        : `No ${stage.label.toLowerCase()} tasks in this run.`}
                    </p>
                  ) : null}
                  {stageTasks.length > 0 ? (
                    <ul className="task-list">
                      {stageTasks.map((task) => (
                        <li key={task.id} className="task-item">
                          <div>
                            <strong>{task.agent}</strong>
                            <span className="muted"> · {task.id}</span>
                          </div>
                          <StatusBadge status={task.status} />
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ol>

          <h3 className="section-title">All tasks</h3>
          {tasks.length === 0 ? (
            <p className="muted">This run did not return any tasks yet.</p>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Agent</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => (
                    <tr key={task.id}>
                      <td>{task.id}</td>
                      <td>{task.agent}</td>
                      <td>
                        <StatusBadge status={task.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {agentDetail ? (
            <div className="agent-detail">
              <h3>Agent run details</h3>
              <dl className="meta-list">
                <dt>Agent</dt>
                <dd>{agentDetail.agent || "—"}</dd>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={agentDetail.status} />
                </dd>
                <dt>Started</dt>
                <dd>{formatDateTime(agentDetail.started_at)}</dd>
                <dt>Completed</dt>
                <dd>{formatDateTime(agentDetail.completed_at)}</dd>
                {agentDetail.confidence !== undefined && agentDetail.confidence !== null ? (
                  <>
                    <dt>Confidence</dt>
                    <dd>{agentDetail.confidence}</dd>
                  </>
                ) : null}
              </dl>
              {agentDetail.error ? <p className="error-text">{String(agentDetail.error)}</p> : null}
              {agentDetail.result && Object.keys(agentDetail.result).length > 0 ? (
                <pre className="json-block">{JSON.stringify(agentDetail.result, null, 2)}</pre>
              ) : (
                <p className="muted">No result payload was returned for this run.</p>
              )}
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
