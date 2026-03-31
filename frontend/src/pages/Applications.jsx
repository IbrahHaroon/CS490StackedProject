import { useEffect, useState } from "react";
import "./Applications.css";

const API = "http://localhost:8000";

const STAGES = ["Interested", "Applied", "Interview", "Offer", "Rejected", "Archived", "Withdrawn"];

const STATUS_COLOR = {
  Interested:  "#4f8ef7",
  Applied:     "#a78bfa",
  Interview:   "#f59e0b",
  Offer:       "#22c55e",
  Rejected:    "#ef4444",
  Archived:    "#6b7280",
  Withdrawn:   "#374151",
};

function Pipeline({ current }) {
  const isTerminal = current === "Rejected" || current === "Archived";
  const active = isTerminal
    ? STAGES.slice(0, 4)
    : STAGES.slice(0, 5);

  const currentIdx = active.indexOf(current);

  return (
    <div className="pipeline">
      {active.map((stage, i) => (
        <div key={stage} className="pipeline-step">
          <div
            className={`pipeline-dot ${i <= currentIdx ? "pipeline-dot-active" : ""}`}
            style={i === currentIdx ? { backgroundColor: STATUS_COLOR[current] } : {}}
          />
          <span className={`pipeline-label ${i === currentIdx ? "pipeline-label-active" : ""}`}>
            {stage}
          </span>
          {i < active.length - 1 && (
            <div className={`pipeline-line ${i < currentIdx ? "pipeline-line-active" : ""}`} />
          )}
        </div>
      ))}
      {isTerminal && (
        <div className="pipeline-step">
          <div className="pipeline-dot pipeline-dot-active" style={{ backgroundColor: STATUS_COLOR[current] }} />
          <span className="pipeline-label pipeline-label-active">{current}</span>
        </div>
      )}
    </div>
  );
}

function ApplicationCard({ app, position, onRemove }) {
  const [expanded, setExpanded] = useState(false);
  const [activity, setActivity] = useState(null);
  const [removing, setRemoving] = useState(false);
  const token = localStorage.getItem("token");

  const loadActivity = async () => {
    if (activity) { setExpanded(!expanded); return; }
    const res = await fetch(`${API}/jobs/applications/${app.job_id}/activity`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setActivity(await res.json());
    setExpanded(true);
  };

  const title    = position?.title    || `Position #${app.position_id}`;

  return (
    <div className="app-card">
      <div className="app-card-header">
        <div className="app-card-info">
          <h3 className="app-card-title">{title}</h3>
          <span className="app-card-meta">Applied {app.application_date}</span>
          <span className="app-card-meta">{app.years_of_experience} yr{app.years_of_experience !== 1 ? "s" : ""} experience</span>
        </div>
        <div className="app-card-right">
          <span
            className="app-status-badge"
            style={{ backgroundColor: STATUS_COLOR[app.application_status] }}
          >
            {app.application_status}
          </span>
          <button className="app-history-btn" onClick={loadActivity}>
            {expanded ? "Hide History ▲" : "View History ▼"}
          </button>
          <button
            className="app-remove-btn"
            disabled={removing}
            onClick={async () => {
              if (!window.confirm("Remove this application?")) return;
              setRemoving(true);
              await fetch(`${API}/jobs/applications/${app.job_id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
              });
              onRemove(app.job_id);
            }}
          >
            {removing ? "Removing…" : "Remove"}
          </button>
        </div>
      </div>

      <Pipeline current={app.application_status} />

      {expanded && activity && (
        <div className="app-activity">
          <h4 className="app-activity-title">Stage History</h4>
          <ul className="app-activity-list">
            {activity.map((a) => (
              <li key={a.activity_id} className="app-activity-item">
                <span
                  className="app-activity-dot"
                  style={{ backgroundColor: STATUS_COLOR[a.stage] || "#888" }}
                />
                <span className="app-activity-stage">{a.stage}</span>
                <span className="app-activity-date">
                  {new Date(a.changed_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function Applications() {
  const [applications, setApplications] = useState([]);
  const [positions, setPositions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("All");
  const token = localStorage.getItem("token");

  useEffect(() => {
    const load = async () => {
      const res = await fetch(`${API}/jobs/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { setError("Failed to load applications."); setLoading(false); return; }

      const apps = await res.json();
      setApplications(apps);

      // Fetch position details for each unique position_id
      const uniqueIds = [...new Set(apps.map((a) => a.position_id))];
      const posMap = {};
      await Promise.all(
        uniqueIds.map(async (id) => {
          const r = await fetch(`${API}/jobs/positions/${id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (r.ok) posMap[id] = await r.json();
        })
      );
      setPositions(posMap);
      setLoading(false);
    };
    load();
  }, []);

  const filtered = filter === "All"
    ? applications.filter((a) => a.application_status !== "Withdrawn")
    : applications.filter((a) => a.application_status === filter);

  return (
    <div className="applications-page">
      <h1>My Applications</h1>

      {error && <p className="applications-error">{error}</p>}

      {!loading && !error && (
        <>
          <div className="app-filters">
            {["All", ...STAGES].map((s) => (
              <button
                key={s}
                className={`app-filter-btn ${filter === s ? "app-filter-btn-active" : ""}`}
                onClick={() => setFilter(s)}
              >
                {s}
                {s !== "All" && (
                  <span className="app-filter-count">
                    {applications.filter((a) => a.application_status === s).length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {filtered.length === 0 ? (
            <p className="applications-placeholder">
              {filter === "All" ? "No applications yet." : `No applications with status "${filter}".`}
            </p>
          ) : (
            <div className="app-list">
              {filtered.map((app) => (
                <ApplicationCard
                  key={app.job_id}
                  app={app}
                  position={positions[app.position_id]}
                  onRemove={(id) => setApplications((prev) => prev.filter((a) => a.job_id !== id))}
                />
              ))}
            </div>
          )}
        </>
      )}

      {loading && <p className="applications-placeholder">Loading…</p>}
    </div>
  );
}

export default Applications;
