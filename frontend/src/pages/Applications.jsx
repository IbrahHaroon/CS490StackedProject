import { useEffect, useState } from "react";
import "./Applications.css";
import StageBadge from "../components/StageBadge";
import DeleteConfirmModal from "../components/DeleteConfirmModal";

const API = "http://localhost:8000";

const STAGES = [
  "Interested",
  "Applied",
  "Interview",
  "Offer",
  "Rejected",
  "Archived",
  "Withdrawn",
];

const STATUS_COLOR = {
  Interested: "#4f8ef7",
  Applied: "#a78bfa",
  Interview: "#f59e0b",
  Offer: "#22c55e",
  Rejected: "#ef4444",
  Archived: "#6b7280",
  Withdrawn: "#374151",
};

function timeAgo(dateStr) {
  if (!dateStr) return null;
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "just now";
}

function Pipeline({ current }) {
  const isTerminal =
    current === "Rejected" || current === "Archived" || current === "Withdrawn";
  const active = isTerminal ? STAGES.slice(0, 4) : STAGES.slice(0, 5);
  const currentIdx = active.indexOf(current);

  return (
    <div className="pipeline">
      {active.map((stage, i) => (
        <div key={stage} className="pipeline-step">
          <div
            className={`pipeline-dot ${i <= currentIdx ? "pipeline-dot-active" : ""}`}
            style={
              i === currentIdx ? { backgroundColor: STATUS_COLOR[current] } : {}
            }
          />
          <span
            className={`pipeline-label ${i === currentIdx ? "pipeline-label-active" : ""}`}
          >
            {stage}
          </span>
          {i < active.length - 1 && (
            <div
              className={`pipeline-line ${i < currentIdx ? "pipeline-line-active" : ""}`}
            />
          )}
        </div>
      ))}
      {isTerminal && (
        <div className="pipeline-step">
          <div
            className="pipeline-dot pipeline-dot-active"
            style={{ backgroundColor: STATUS_COLOR[current] }}
          />
          <span className="pipeline-label pipeline-label-active">{current}</span>
        </div>
      )}
    </div>
  );
}

function ApplicationCard({ app, position, onRemove }) {
  const [expanded, setExpanded] = useState(false);
  const [activity, setActivity] = useState(null);
  const [activityLoaded, setActivityLoaded] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [showCoverLetter, setShowCoverLetter] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const token = localStorage.getItem("token");

  // S2-007 — Deadline & Recruiter Notes
  const [showDetails, setShowDetails] = useState(false);
  const [editingDetails, setEditingDetails] = useState(false);
  const [detailValues, setDetailValues] = useState({
    deadline: app.deadline || "",
    recruiter_notes: app.recruiter_notes || "",
  });
  const [detailSaving, setDetailSaving] = useState(false);
  const [detailError, setDetailError] = useState("");

  // S2-012 — Follow-Ups
  const [showFollowUps, setShowFollowUps] = useState(false);
  const [followUps, setFollowUps] = useState([]);
  const [followUpsLoaded, setFollowUpsLoaded] = useState(false);
  const [newFollowUp, setNewFollowUp] = useState({
    description: "",
    due_date: "",
  });
  const [addingFollowUp, setAddingFollowUp] = useState(false);
  const [followUpError, setFollowUpError] = useState("");

  const loadActivity = async () => {
    if (activityLoaded) {
      setExpanded((v) => !v);
      return;
    }
    try {
      const res = await fetch(
        `${API}/jobs/applications/${app.job_id}/activity`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      if (res.ok) setActivity(await res.json());
    } catch (err) {
      console.error("Failed to load activity:", err);
    }

    setActivityLoaded(true);
    setExpanded(true);
  };

  const generateCoverLetter = async () => {
    setIsGenerating(true);
    const title = position?.title || "this role";
    const company = position?.company_name || "your company";
    const generated = `Dear Hiring Manager,

I am excited to apply for the ${title} position at ${company}. My background and experience make me a strong candidate for this opportunity.

Through my previous work and projects, I have developed relevant technical and problem-solving skills that align with the responsibilities of this role. I am especially interested in contributing to ${company} and continuing to grow in a position like ${title}.

I am eager to bring my motivation, adaptability, and willingness to learn to your team. Thank you for your time and consideration. I would welcome the opportunity to discuss how my experience and interests align with this position.

Sincerely,
[Your Name]`;
    setCoverLetter(generated);
    setShowCoverLetter(true);
    setIsGenerating(false);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(coverLetter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // S2-007 — save deadline + recruiter notes
  const saveDetails = async () => {
    setDetailSaving(true);
    setDetailError("");
    try {
      const res = await fetch(`${API}/jobs/applications/${app.job_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(detailValues),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setDetailError(err.detail || "Failed to save.");
      } else {
        setEditingDetails(false);
      }
    } catch {
      setDetailError("Failed to save.");
    } finally {
      setDetailSaving(false);
    }
  };

  // S2-012 — lazy-load follow-ups (mirrors loadActivity pattern)
  const loadFollowUps = async () => {
    if (!showFollowUps && !followUpsLoaded) {
      try {
        const res = await fetch(`${API}/jobs/${app.job_id}/followups`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) setFollowUps(await res.json());
      } catch {
        // leave empty on error
      }
      setFollowUpsLoaded(true);
    }
    setShowFollowUps((v) => !v);
  };

  const createFollowUp = async () => {
    if (!newFollowUp.description.trim()) {
      setFollowUpError("Description is required.");
      return;
    }
    try {
      const res = await fetch(`${API}/jobs/${app.job_id}/followups`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          job_id: app.job_id,
          description: newFollowUp.description,
          due_date: newFollowUp.due_date || null,
        }),
      });
      if (res.ok) {
        const created = await res.json();
        setFollowUps((prev) => [...prev, created]);
        setNewFollowUp({ description: "", due_date: "" });
        setFollowUpError("");
        setAddingFollowUp(false);
      }
    } catch {
      setFollowUpError("Failed to create follow-up.");
    }
  };

  const toggleComplete = async (fu) => {
    try {
      const res = await fetch(`${API}/followups/${fu.followup_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ completed: !fu.completed }),
      });
      if (res.ok) {
        const updated = await res.json();
        setFollowUps((prev) =>
          prev.map((f) => (f.followup_id === fu.followup_id ? updated : f))
        );
      }
    } catch {
      // silently fail — checkbox will snap back on next load
    }
  };

  const deleteFollowUp = async (followup_id) => {
    try {
      const res = await fetch(`${API}/followups/${followup_id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setFollowUps((prev) =>
          prev.filter((f) => f.followup_id !== followup_id)
        );
      }
    } catch {
      // silently fail
    }
  };

  const title = position?.title || `Position #${app.position_id}`;
  const company = position?.company_name || "";

  return (
    <div
      className="app-card"
      style={{
        border:
          app.application_status === "Interview"
            ? "2px solid #f59e0b"
            : app.application_status === "Offer"
              ? "2px solid #22c55e"
              : "1px solid var(--border-light)",
        boxShadow:
          app.application_status === "Offer"
            ? "0 0 12px rgba(34,197,94,0.25)"
            : app.application_status === "Interview"
              ? "0 0 8px rgba(245,158,11,0.25)"
              : "none",
      }}
    >
      <div className="app-card-header">
        <div className="app-card-info">
          <h3 className="app-card-title">{title}</h3>
          {company && (
            <span className="app-card-meta app-card-company">{company}</span>
          )}
          <span className="app-card-meta">Applied {app.application_date}</span>
          <span className="app-card-meta">
            {app.years_of_experience} yr
            {app.years_of_experience !== 1 ? "s" : ""} experience
          </span>
          {stageChangedLabel && (
            <span className="app-card-meta app-card-stage-time">
              Stage updated {stageChangedLabel}
            </span>
          )}
        </div>

        <div className="app-card-right">
          <StageBadge status={app.application_status} />
          <button className="app-history-btn" onClick={loadActivity}>
            {expanded ? "Hide History ▲" : "View History ▼"}
          </button>
          <button className="app-secondary-btn" onClick={generateCoverLetter}>
            {isGenerating ? "Generating…" : "Generate Cover Letter"}
          </button>
          <button className="app-remove-btn" onClick={onRemove}>
            Remove
          </button>
        </div>
      </div>

      <Pipeline current={app.application_status} />

      {/* S2-007 — Deadline & Recruiter Notes */}
      <div className="details-section">
        <button
          className="app-history-btn details-toggle"
          onClick={() => setShowDetails((v) => !v)}
        >
          Details {showDetails ? "▾" : "▸"}
        </button>
        {showDetails && (
          <div className="details-body">
            {!editingDetails ? (
              <>
                <div className="details-row">
                  <span className="details-label">Deadline</span>
                  <span className="details-value">
                    {detailValues.deadline
                      ? new Date(
                          detailValues.deadline + "T00:00:00"
                        ).toLocaleDateString()
                      : "—"}
                  </span>
                </div>
                <div className="details-row">
                  <span className="details-label">Recruiter Notes</span>
                  <span className="details-value">
                    {detailValues.recruiter_notes || (
                      <em style={{ color: "#6b7280" }}>No notes yet</em>
                    )}
                  </span>
                </div>
                <button
                  className="app-history-btn"
                  style={{ marginTop: "8px" }}
                  onClick={() => setEditingDetails(true)}
                >
                  Edit
                </button>
              </>
            ) : (
              <div className="details-edit-form">
                <label className="details-label">Deadline</label>
                <input
                  type="date"
                  className="details-input"
                  value={detailValues.deadline}
                  onChange={(e) =>
                    setDetailValues((prev) => ({
                      ...prev,
                      deadline: e.target.value,
                    }))
                  }
                />
                <label className="details-label">
                  Recruiter / Contact Notes
                </label>
                <textarea
                  className="details-textarea"
                  value={detailValues.recruiter_notes}
                  onChange={(e) =>
                    setDetailValues((prev) => ({
                      ...prev,
                      recruiter_notes: e.target.value,
                    }))
                  }
                  rows={3}
                />
                {detailError && (
                  <p
                    style={{
                      color: "#ef4444",
                      fontSize: "13px",
                      margin: "4px 0",
                    }}
                  >
                    {detailError}
                  </p>
                )}
                <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                  <button
                    className="app-history-btn"
                    onClick={saveDetails}
                    disabled={detailSaving}
                  >
                    {detailSaving ? "Saving…" : "Save"}
                  </button>
                  <button
                    className="app-history-btn"
                    onClick={() => {
                      setEditingDetails(false);
                      setDetailError("");
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* S2-012 — Follow-Up & Reminder Tracking */}
      <div className="followup-section">
        <button
          className="app-history-btn followup-toggle"
          onClick={loadFollowUps}
        >
          Follow-Ups{followUps.length > 0 ? ` (${followUps.length})` : ""}{" "}
          {showFollowUps ? "▾" : "▸"}
        </button>
        {showFollowUps && (
          <div className="followup-body">
            {followUps.length === 0 ? (
              <p className="followup-empty">No follow-ups yet.</p>
            ) : (
              <ul className="followup-list">
                {followUps.map((fu) => (
                  <li key={fu.followup_id} className="followup-item">
                    <input
                      type="checkbox"
                      checked={fu.completed}
                      onChange={() => toggleComplete(fu)}
                      className="followup-checkbox"
                    />
                    <span
                      className={
                        fu.completed
                          ? "followup-desc followup-done"
                          : "followup-desc"
                      }
                    >
                      {fu.description}
                    </span>
                    {fu.due_date && (
                      <span className="followup-date">
                        {new Date(
                          fu.due_date + "T00:00:00"
                        ).toLocaleDateString()}
                      </span>
                    )}
                    <button
                      className="followup-delete-btn"
                      onClick={() => deleteFollowUp(fu.followup_id)}
                      title="Delete"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {addingFollowUp ? (
              <div className="followup-add-form">
                <input
                  type="text"
                  className="followup-input"
                  placeholder="Description (required)"
                  value={newFollowUp.description}
                  onChange={(e) =>
                    setNewFollowUp((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                />
                <input
                  type="date"
                  className="followup-input"
                  value={newFollowUp.due_date}
                  onChange={(e) =>
                    setNewFollowUp((prev) => ({
                      ...prev,
                      due_date: e.target.value,
                    }))
                  }
                />
                {followUpError && (
                  <p
                    style={{
                      color: "#ef4444",
                      fontSize: "13px",
                      margin: "4px 0",
                    }}
                  >
                    {followUpError}
                  </p>
                )}
                <div style={{ display: "flex", gap: "8px" }}>
                  <button className="app-history-btn" onClick={createFollowUp}>
                    Save
                  </button>
                  <button
                    className="app-history-btn"
                    onClick={() => {
                      setAddingFollowUp(false);
                      setNewFollowUp({ description: "", due_date: "" });
                      setFollowUpError("");
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                className="app-history-btn"
                style={{ marginTop: "8px" }}
                onClick={() => setAddingFollowUp(true)}
              >
                + Add Follow-Up
              </button>
            )}
          </div>
        )}
      </div>

      {showCoverLetter && (
        <div className="cover-letter-box">
          <div className="cover-letter-header">
            <h4 className="cover-letter-title">Cover Letter Draft</h4>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                className="app-history-btn"
                onClick={copyToClipboard}
                disabled={!coverLetter}
              >
                {copied ? "Copied!" : "Copy to Clipboard"}
              </button>
              <button
                className="app-history-btn"
                onClick={() => setShowCoverLetter((prev) => !prev)}
              >
                {showCoverLetter ? "Hide Draft" : "Show Draft"}
              </button>
            </div>
          </div>
          <textarea
            className="cover-letter-textarea"
            value={coverLetter}
            onChange={(e) => setCoverLetter(e.target.value)}
          />
        </div>
      )}

      {expanded && (
        <div className="app-activity">
          <h4 className="app-activity-title">Stage History</h4>
          {activity && activity.length > 0 ? (
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
          ) : (
            <p
              style={{
                color: "var(--text-muted)",
                fontSize: "0.85rem",
                margin: "4px 0 0",
              }}
            >
              No history yet.
            </p>
          )}
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
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API}/jobs/dashboard`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (!res.ok) {
          setError("Failed to load applications. Please sign in.");
          setLoading(false);
          return;
        }

        const apps = await res.json();
        setApplications(apps);

        const uniqueIds = [...new Set(apps.map((a) => a.position_id))];
        const posMap = {};
        await Promise.all(
          uniqueIds.map(async (id) => {
            const r = await fetch(`${API}/jobs/positions/${id}`, {
              headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
            if (r.ok) posMap[id] = await r.json();
          })
        );
        setPositions(posMap);
        setLoading(false);
      } catch (err) {
        setError("Failed to load applications.");
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const filtered = applications.filter((a) => {
    const matchesStage =
      filter === "All"
        ? a.application_status !== "Withdrawn"
        : a.application_status === filter;

    const positionTitle = positions[a.position_id]?.title || "";
    const companyName = positions[a.position_id]?.company_name || "";
    const q = search.toLowerCase().trim();
    const matchesSearch =
      !q ||
      positionTitle.toLowerCase().includes(q) ||
      companyName.toLowerCase().includes(q);

    return matchesStage && matchesSearch;
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      setIsDeleting(true);
      await fetch(`${API}/jobs/applications/${deleteTarget.job_id}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).catch(() => {});
      setApplications((prev) =>
        prev.filter((a) => a.job_id !== deleteTarget.job_id)
      );
    } catch (err) {
      console.error("Failed to delete application:", err);
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="applications-page">
      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        title="Remove this application?"
        message={
          deleteTarget
            ? `Are you sure you want to remove the ${
                positions[deleteTarget.position_id]?.title || "selected"
              } application? This action cannot be undone.`
            : ""
        }
        onCancel={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
      />

      <h1>My Applications</h1>

      {error && <p className="applications-error">{error}</p>}

      {!loading && !error && (
        <>
          <div className="app-controls">
            <div className="app-search-row">
              <input
                type="text"
                placeholder="Search by title or company…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="app-search"
              />
              <button
                type="button"
                className="app-clear-btn"
                disabled={!search && filter === "All"}
                onClick={() => {
                  setFilter("All");
                  setSearch("");
                }}
              >
                Clear
              </button>
            </div>

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
                      {
                        applications.filter((a) => a.application_status === s)
                          .length
                      }
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <p className="applications-placeholder">
              {filter === "All"
                ? "No applications yet."
                : `No applications with status "${filter}".`}
            </p>
          ) : (
            <div className="app-list">
              {filtered.map((app) => (
                <ApplicationCard
                  key={app.job_id}
                  app={app}
                  position={positions[app.position_id]}
                  onRemove={() => setDeleteTarget(app)}
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
