import { useEffect, useState } from "react";
import "./Applications.css";
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

const EVENT_TYPE_META = {
  stage_change: { color: null, icon: "●", label: null },
  follow_up: { color: "#06b6d4", icon: "🔔", label: "Follow-up" },
  interview: { color: "#f59e0b", icon: "📅", label: "Interview" },
  outcome: { color: "#22c55e", icon: "🏁", label: "Outcome" },
};

function Pipeline({ current }) {
  const isTerminal = current === "Rejected" || current === "Archived";
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
          <span className="pipeline-label pipeline-label-active">
            {current}
          </span>
        </div>
      )}
    </div>
  );
}

function ApplicationCard({ app, position, onRemove, onStageChange }) {
  const [expanded, setExpanded] = useState(false);
  const [activity, setActivity] = useState(null);
  const [activityLoaded, setActivityLoaded] = useState(false);
  const [updatingStage, setUpdatingStage] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [showCoverLetter, setShowCoverLetter] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [genError, setGenError] = useState("");
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

  // Interviews
  const [showInterviews, setShowInterviews] = useState(false);
  const [interviews, setInterviews] = useState([]);
  const [interviewsLoaded, setInterviewsLoaded] = useState(false);
  const [addingInterview, setAddingInterview] = useState(false);
  const [newInterview, setNewInterview] = useState({
    round_type: "",
    scheduled_at: "",
  });
  const [interviewError, setInterviewError] = useState("");

  // Outcome
  const [showOutcome, setShowOutcome] = useState(false);
  const [outcome, setOutcome] = useState(null);
  const [outcomeLoaded, setOutcomeLoaded] = useState(false);
  const [addingOutcome, setAddingOutcome] = useState(false);
  const [newOutcome, setNewOutcome] = useState({
    outcome_state: "",
    outcome_notes: "",
  });
  const [outcomeError, setOutcomeError] = useState("");
  const OUTCOME_STATES = [
    "Applied",
    "Rejected",
    "Offer",
    "Accepted",
    "Withdrawn",
  ];

  const handleStageChange = async (newStage) => {
    if (newStage === app.application_status || updatingStage) return;
    const previousStage = app.application_status;
    setUpdatingStage(true);
    onStageChange(app.job_id, newStage);
    try {
      const res = await fetch(`${API}/jobs/applications/${app.job_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ application_status: newStage }),
      });
      if (!res.ok) {
        const detail = await res.text();
        console.error(
          `Stage change failed (${res.status}) for job ${app.job_id}:`,
          detail
        );
        onStageChange(app.job_id, previousStage);
      } else {
        setActivity(null);
        setActivityLoaded(false);
      }
    } catch (err) {
      console.error("Stage change request errored:", err);
      onStageChange(app.job_id, previousStage);
    } finally {
      setUpdatingStage(false);
    }
  };

  const loadActivity = async () => {
    if (activityLoaded) {
      setExpanded((v) => !v);
      return;
    }

    try {
      const res = await fetch(
        `${API}/jobs/applications/${app.job_id}/activity`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );

      if (res.ok) {
        setActivity(await res.json());
      }
    } catch (err) {
      console.error("Failed to load activity:", err);
    }

    setActivityLoaded(true);
    setExpanded(true);
  };

  const generateCoverLetter = async () => {
    setIsGenerating(true);
    setGenError("");
    try {
      const res = await fetch(`${API}/documents/generate-cover-letter`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ job_id: app.job_id }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setGenError(err.detail || "Failed to generate cover letter.");
        setShowCoverLetter(true);
        return;
      }
      const data = await res.json();
      setCoverLetter(data.content || "");
      setShowCoverLetter(true);
    } catch {
      setGenError("Network error — could not reach the server.");
      setShowCoverLetter(true);
    } finally {
      setIsGenerating(false);
    }
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

  const loadInterviews = async () => {
    if (!showInterviews && !interviewsLoaded) {
      try {
        const res = await fetch(`${API}/jobs/${app.job_id}/interviews`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) setInterviews(await res.json());
      } catch {
        // leave empty on error
      }
      setInterviewsLoaded(true);
    }
    setShowInterviews((v) => !v);
  };

  const createInterview = async () => {
    if (!newInterview.round_type.trim()) {
      setInterviewError("Round type is required.");
      return;
    }
    if (!newInterview.scheduled_at) {
      setInterviewError("Date & time is required.");
      return;
    }
    try {
      const res = await fetch(`${API}/jobs/${app.job_id}/interviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          job_id: app.job_id,
          round_type: newInterview.round_type,
          scheduled_at: newInterview.scheduled_at,
        }),
      });
      if (res.ok) {
        const created = await res.json();
        setInterviews((prev) => [...prev, created]);
        setNewInterview({ round_type: "", scheduled_at: "" });
        setInterviewError("");
        setAddingInterview(false);
        // Reset timeline so new event appears on next load
        setActivity(null);
        setActivityLoaded(false);
      } else {
        const detail = await res.json().catch(() => ({}));
        setInterviewError(detail.detail || "Failed to save interview.");
      }
    } catch {
      setInterviewError("Failed to save interview.");
    }
  };

  const deleteInterview = async (interview_id) => {
    try {
      const res = await fetch(`${API}/interviews/${interview_id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setInterviews((prev) =>
          prev.filter((i) => i.interview_id !== interview_id)
        );
      }
    } catch {
      // silently fail
    }
  };

  const loadOutcome = async () => {
    if (!showOutcome && !outcomeLoaded) {
      try {
        const res = await fetch(`${API}/jobs/${app.job_id}/outcome`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) setOutcome(await res.json());
        // 404 just means no outcome yet — leave as null
      } catch {
        // leave empty
      }
      setOutcomeLoaded(true);
    }
    setShowOutcome((v) => !v);
  };

  const OUTCOME_TO_STAGE = {
    Accepted: "Offer",
    Offer: "Offer",
    Rejected: "Rejected",
    Withdrawn: "Withdrawn",
    Applied: "Applied",
  };

  const saveOutcome = async () => {
    if (!newOutcome.outcome_state) {
      setOutcomeError("Please select an outcome.");
      return;
    }
    try {
      const method = outcome ? "PUT" : "POST";
      const url = outcome
        ? `${API}/outcome/${outcome.outcome_id}`
        : `${API}/jobs/${app.job_id}/outcome`;
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          job_id: app.job_id,
          outcome_state: newOutcome.outcome_state,
          outcome_notes: newOutcome.outcome_notes || null,
        }),
      });
      if (res.ok) {
        const saved = await res.json();
        setOutcome(saved);
        setNewOutcome({ outcome_state: "", outcome_notes: "" });
        setOutcomeError("");
        setAddingOutcome(false);
        setActivity(null);
        setActivityLoaded(false);

        // Auto-update the application stage to match the outcome
        const targetStage = OUTCOME_TO_STAGE[newOutcome.outcome_state];
        if (targetStage && targetStage !== app.application_status) {
          await fetch(`${API}/jobs/applications/${app.job_id}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ application_status: targetStage }),
          });
          onStageChange(app.job_id, targetStage);
        }
      } else {
        const detail = await res.json().catch(() => ({}));
        setOutcomeError(detail.detail || "Failed to save outcome.");
      }
    } catch {
      setOutcomeError("Failed to save outcome.");
    }
  };

  const deleteOutcome = async () => {
    if (!outcome) return;
    try {
      const res = await fetch(`${API}/outcome/${outcome.outcome_id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setOutcome(null);
        setOutcomeLoaded(false);
      }
    } catch {
      // silently fail
    }
  };

  const title = position?.title || `Position #${app.position_id}`;
  const company = position?.company_name;

  return (
    <div
      className="app-card"
      style={{
        border:
          app.application_status === "Interview"
            ? "2px solid orange"
            : app.application_status === "Offer"
              ? "2px solid green"
              : "1px solid #333",
        boxShadow: "none",
        transition: "0.2s ease-in-out",
      }}
    >
      <div className="app-card-header">
        <div className="app-card-info">
          <h3 className="app-card-title">{title}</h3>
          {company && <span className="app-card-company">{company}</span>}
          <span className="app-card-meta">Applied {app.application_date}</span>
          <span className="app-card-meta">
            {app.years_of_experience} yr
            {app.years_of_experience !== 1 ? "s" : ""} experience
          </span>
        </div>

        <div className="app-card-right">
          <select
            className="app-stage-select"
            value={app.application_status}
            disabled={updatingStage}
            onChange={(e) => handleStageChange(e.target.value)}
            style={{
              borderColor: STATUS_COLOR[app.application_status],
              color: STATUS_COLOR[app.application_status],
            }}
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <button className="app-history-btn" onClick={loadActivity}>
            {expanded ? "Hide History ▲" : "View History ▼"}
          </button>
          <button className="app-secondary-btn" onClick={generateCoverLetter}>
            {isGenerating ? "Generating..." : "Generate Cover Letter"}
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

      {/* Interviews */}
      <div className="followup-section">
        <button
          className="app-history-btn followup-toggle"
          onClick={loadInterviews}
        >
          Interviews{interviews.length > 0 ? ` (${interviews.length})` : ""}{" "}
          {showInterviews ? "▾" : "▸"}
        </button>
        {showInterviews && (
          <div className="followup-body">
            {interviews.length === 0 ? (
              <p className="followup-empty">No interviews scheduled yet.</p>
            ) : (
              <ul className="followup-list">
                {interviews.map((iv) => (
                  <li key={iv.interview_id} className="followup-item">
                    <span className="followup-desc">📅 {iv.round_type}</span>
                    <span className="followup-date">
                      {new Date(iv.scheduled_at).toLocaleString()}
                    </span>
                    <button
                      className="followup-delete-btn"
                      onClick={() => deleteInterview(iv.interview_id)}
                      title="Delete"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {addingInterview ? (
              <div className="followup-add-form">
                <input
                  type="text"
                  className="followup-input"
                  placeholder="Round type (e.g. Technical, HR)"
                  value={newInterview.round_type}
                  onChange={(e) =>
                    setNewInterview((prev) => ({
                      ...prev,
                      round_type: e.target.value,
                    }))
                  }
                />
                <input
                  type="datetime-local"
                  className="followup-input"
                  value={newInterview.scheduled_at}
                  onChange={(e) =>
                    setNewInterview((prev) => ({
                      ...prev,
                      scheduled_at: e.target.value,
                    }))
                  }
                />
                {interviewError && (
                  <p
                    style={{
                      color: "#ef4444",
                      fontSize: "13px",
                      margin: "4px 0",
                    }}
                  >
                    {interviewError}
                  </p>
                )}
                <div style={{ display: "flex", gap: "8px" }}>
                  <button className="app-history-btn" onClick={createInterview}>
                    Save
                  </button>
                  <button
                    className="app-history-btn"
                    onClick={() => {
                      setAddingInterview(false);
                      setNewInterview({ round_type: "", scheduled_at: "" });
                      setInterviewError("");
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
                onClick={() => setAddingInterview(true)}
              >
                + Schedule Interview
              </button>
            )}
          </div>
        )}
      </div>

      {/* Outcome */}
      <div className="followup-section">
        <button
          className="app-history-btn followup-toggle"
          onClick={loadOutcome}
        >
          Outcome{outcome ? ` — ${outcome.outcome_state}` : ""}{" "}
          {showOutcome ? "▾" : "▸"}
        </button>
        {showOutcome && (
          <div className="followup-body">
            {outcome && !addingOutcome ? (
              <div
                className="followup-item"
                style={{
                  flexDirection: "column",
                  alignItems: "flex-start",
                  gap: "4px",
                }}
              >
                <span className="followup-desc">
                  🏁 {outcome.outcome_state}
                </span>
                {outcome.outcome_notes && (
                  <span className="followup-date">{outcome.outcome_notes}</span>
                )}
                <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
                  <button
                    className="app-history-btn"
                    onClick={() => {
                      setNewOutcome({
                        outcome_state: outcome.outcome_state,
                        outcome_notes: outcome.outcome_notes || "",
                      });
                      setAddingOutcome(true);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="followup-delete-btn"
                    onClick={deleteOutcome}
                  >
                    ✕ Remove
                  </button>
                </div>
              </div>
            ) : !addingOutcome ? (
              <p className="followup-empty">No outcome recorded yet.</p>
            ) : null}

            {addingOutcome ? (
              <div className="followup-add-form">
                <select
                  className="followup-input"
                  value={newOutcome.outcome_state}
                  onChange={(e) =>
                    setNewOutcome((prev) => ({
                      ...prev,
                      outcome_state: e.target.value,
                    }))
                  }
                >
                  <option value="">Select outcome…</option>
                  {OUTCOME_STATES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  className="followup-input"
                  placeholder="Notes (optional)"
                  value={newOutcome.outcome_notes}
                  onChange={(e) =>
                    setNewOutcome((prev) => ({
                      ...prev,
                      outcome_notes: e.target.value,
                    }))
                  }
                />
                {outcomeError && (
                  <p
                    style={{
                      color: "#ef4444",
                      fontSize: "13px",
                      margin: "4px 0",
                    }}
                  >
                    {outcomeError}
                  </p>
                )}
                <div style={{ display: "flex", gap: "8px" }}>
                  <button className="app-history-btn" onClick={saveOutcome}>
                    Save
                  </button>
                  <button
                    className="app-history-btn"
                    onClick={() => {
                      setAddingOutcome(false);
                      setNewOutcome({ outcome_state: "", outcome_notes: "" });
                      setOutcomeError("");
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
                onClick={() => setAddingOutcome(true)}
              >
                + Record Outcome
              </button>
            )}
          </div>
        )}
      </div>

      {showCoverLetter && (
        <div className="cover-letter-box">
          <div className="cover-letter-header">
            <h4 className="cover-letter-title">AI Cover Letter</h4>
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
                onClick={() => {
                  setShowCoverLetter(false);
                  setGenError("");
                }}
              >
                Hide
              </button>
            </div>
          </div>
          {genError ? (
            <p
              style={{ color: "#ef4444", fontSize: "13px", margin: "8px 0 0" }}
            >
              {genError}
            </p>
          ) : (
            <>
              <p
                style={{
                  color: "var(--text-muted)",
                  fontSize: "12px",
                  margin: "4px 0 8px",
                }}
              >
                Saved to your Document Library.
              </p>
              <textarea
                className="cover-letter-textarea"
                value={coverLetter}
                onChange={(e) => setCoverLetter(e.target.value)}
              />
            </>
          )}
        </div>
      )}

      {expanded && (
        <div className="app-activity">
          <h4 className="app-activity-title">Activity Timeline</h4>
          {activity && activity.length > 0 ? (
            <ul className="app-activity-list">
              {activity.map((a) => {
                const meta =
                  EVENT_TYPE_META[a.event_type] || EVENT_TYPE_META.stage_change;
                const dotColor = meta.color || STATUS_COLOR[a.stage] || "#888";
                return (
                  <li key={a.activity_id} className="app-activity-item">
                    <span
                      className="app-activity-dot"
                      style={{ backgroundColor: dotColor }}
                      title={meta.label || a.stage}
                    >
                      {meta.icon !== "●" ? meta.icon : ""}
                    </span>
                    <span className="app-activity-stage">
                      {meta.label ? `${meta.label}: ` : ""}
                      {a.stage}
                    </span>
                    {a.notes && (
                      <span className="app-activity-notes">{a.notes}</span>
                    )}
                    <span className="app-activity-date">
                      {new Date(a.changed_at).toLocaleString()}
                    </span>
                  </li>
                );
              })}
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

function HistoryOverlay({ applications, positions, onClose, onRestore }) {
  const [allActivity, setAllActivity] = useState([]);
  const [activityByJob, setActivityByJob] = useState({});
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [restoringJobId, setRestoringJobId] = useState(null);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const loadAll = async () => {
      const results = [];
      const byJob = {};
      await Promise.all(
        applications.map(async (app) => {
          try {
            const res = await fetch(
              `${API}/jobs/applications/${app.job_id}/activity`,
              {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
              }
            );
            if (res.ok) {
              const activities = await res.json();
              const pos = positions[app.position_id];
              const title = pos?.title || `Position #${app.position_id}`;
              byJob[app.job_id] = activities;
              activities.forEach((a) =>
                results.push({ ...a, jobTitle: title, job_id: app.job_id })
              );
            }
          } catch {
            /* skip */
          }
        })
      );
      results.sort((a, b) => new Date(b.changed_at) - new Date(a.changed_at));
      setAllActivity(results);
      setActivityByJob(byJob);
      setLoadingHistory(false);
    };
    loadAll();
  }, [applications, positions, token]);

  // A job is "restorable" from history if it's currently Archived. The current
  // state is looked up by job_id so the button appears next to the Archived
  // timeline entry regardless of which stage-change row the user is looking at.
  const currentStatusById = Object.fromEntries(
    applications.map((a) => [a.job_id, a.application_status])
  );

  const handleRestore = async (jobId) => {
    setRestoringJobId(jobId);
    const history = activityByJob[jobId] || [];
    const sorted = [...history].sort(
      (a, b) => new Date(b.changed_at) - new Date(a.changed_at)
    );
    const previous = sorted.find(
      (h) => h.stage && h.stage !== "Archived" && h.stage !== "Withdrawn"
    );
    const targetStage = previous?.stage || "Applied";

    try {
      const res = await fetch(`${API}/jobs/applications/${jobId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ application_status: targetStage }),
      });
      if (!res.ok) {
        const detail = await res.text();
        console.error(
          `Restore failed (${res.status}) for job ${jobId}:`,
          detail
        );
        return;
      }
      onRestore(jobId, targetStage);
    } catch (err) {
      console.error("Restore request errored:", err);
    } finally {
      setRestoringJobId(null);
    }
  };

  return (
    <div className="history-overlay" onClick={onClose}>
      <div className="history-modal" onClick={(e) => e.stopPropagation()}>
        <button className="history-close-btn" onClick={onClose}>
          &times;
        </button>
        <h2 className="history-modal-title">Application History</h2>

        <h3 className="history-section-title">Activity Timeline</h3>
        {loadingHistory ? (
          <p className="applications-placeholder">Loading history...</p>
        ) : allActivity.length === 0 ? (
          <p className="applications-placeholder">No activity recorded yet.</p>
        ) : (
          <ul className="app-activity-list">
            {allActivity.map((a, i) => {
              const isArchivedEntry = a.stage === "Archived";
              const isWithdrawnEntry = a.stage === "Withdrawn";
              const isCurrentlyArchived =
                currentStatusById[a.job_id] === "Archived";
              const isCurrentlyWithdrawn =
                currentStatusById[a.job_id] === "Withdrawn";
              const showRestore =
                (isArchivedEntry && isCurrentlyArchived) ||
                (isWithdrawnEntry && isCurrentlyWithdrawn);
              const meta =
                EVENT_TYPE_META[a.event_type] || EVENT_TYPE_META.stage_change;
              const dotColor = meta.color || STATUS_COLOR[a.stage] || "#888";
              return (
                <li key={`${a.activity_id}-${i}`} className="history-item">
                  <span
                    className="app-activity-dot"
                    style={{ backgroundColor: dotColor }}
                    title={meta.label || a.stage}
                  >
                    {meta.icon !== "●" ? meta.icon : ""}
                  </span>
                  <span className="history-job-title">{a.jobTitle}</span>
                  <span className="app-activity-stage">
                    {meta.label ? `${meta.label}: ` : ""}
                    {a.stage}
                  </span>
                  {a.notes && (
                    <span className="app-activity-notes">{a.notes}</span>
                  )}
                  <span className="app-activity-date">
                    {new Date(a.changed_at).toLocaleString()}
                  </span>
                  {showRestore && (
                    <button
                      className="app-history-btn history-restore-btn"
                      disabled={restoringJobId === a.job_id}
                      onClick={() => handleRestore(a.job_id)}
                    >
                      {restoringJobId === a.job_id ? "Restoring…" : "Restore"}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

function AddJobModal({ onClose, onAdded }) {
  const [form, setForm] = useState({
    company_name: "",
    title: "",
    location: "",
    salary: "",
    description: "",
    application_status: "Interested",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const token = localStorage.getItem("token");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company_name.trim() || !form.title.trim()) {
      setError("Company name and job title are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const body = {
        company_name: form.company_name.trim(),
        title: form.title.trim(),
        location: form.location.trim() || null,
        salary: form.salary ? parseFloat(form.salary) : null,
        description: form.description.trim() || null,
        application_status: form.application_status,
      };
      const res = await fetch(`${API}/jobs/manual`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        setError(detail.detail || "Failed to save job.");
        return;
      }
      const newApp = await res.json();
      onAdded(newApp);
      onClose();
    } catch {
      setError("Could not reach the server.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="history-overlay" onClick={onClose}>
      <div
        className="history-modal"
        style={{ maxWidth: "480px" }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="history-close-btn" onClick={onClose}>
          &times;
        </button>
        <h2 className="history-modal-title">Add Job to Track</h2>
        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "12px" }}
        >
          <div>
            <label className="details-label">Company Name *</label>
            <input
              className="details-input"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.company_name}
              onChange={(e) =>
                setForm((p) => ({ ...p, company_name: e.target.value }))
              }
              placeholder="e.g. Google"
            />
          </div>
          <div>
            <label className="details-label">Job Title *</label>
            <input
              className="details-input"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.title}
              onChange={(e) =>
                setForm((p) => ({ ...p, title: e.target.value }))
              }
              placeholder="e.g. Software Engineer"
            />
          </div>
          <div>
            <label className="details-label">Location</label>
            <input
              className="details-input"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.location}
              onChange={(e) =>
                setForm((p) => ({ ...p, location: e.target.value }))
              }
              placeholder="e.g. New York, NY"
            />
          </div>
          <div>
            <label className="details-label">Salary</label>
            <input
              type="number"
              className="details-input"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.salary}
              onChange={(e) =>
                setForm((p) => ({ ...p, salary: e.target.value }))
              }
              placeholder="e.g. 120000"
              min="0"
            />
          </div>
          <div>
            <label className="details-label">Notes / Description</label>
            <textarea
              className="details-textarea"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.description}
              onChange={(e) =>
                setForm((p) => ({ ...p, description: e.target.value }))
              }
              rows={3}
              placeholder="Any notes about the job..."
            />
          </div>
          <div>
            <label className="details-label">Initial Status</label>
            <select
              className="app-stage-select"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.application_status}
              onChange={(e) =>
                setForm((p) => ({ ...p, application_status: e.target.value }))
              }
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          {error && (
            <p style={{ color: "#ef4444", fontSize: "13px", margin: "0" }}>
              {error}
            </p>
          )}
          <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
            <button
              type="submit"
              className="app-history-btn"
              disabled={saving}
              style={{ background: "#4f8ef7", color: "#fff", border: "none" }}
            >
              {saving ? "Saving…" : "Save Job"}
            </button>
            <button type="button" className="app-history-btn" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
      </div>
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
  const [showHistory, setShowHistory] = useState(false);
  const [showAddJob, setShowAddJob] = useState(false);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API}/jobs/dashboard`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (!res.ok) {
          const detail = await res.text();
          console.error(`Dashboard load failed (${res.status}):`, detail);
          setApplications([]);
          setPositions({});
          setError("Could not load applications. Please sign in again.");
          setLoading(false);
          return;
        }

        const apps = await res.json();
        const safeApps = apps || [];
        setApplications(safeApps);

        // Fetch all positions in one request to avoid exhausting the DB connection pool
        const posMap = {};
        if (safeApps.length > 0) {
          const pr = await fetch(`${API}/jobs/positions/?include_manual=true`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });
          if (pr.ok) {
            const allPositions = await pr.json();
            const neededIds = new Set(safeApps.map((a) => a.position_id));
            for (const p of allPositions) {
              if (neededIds.has(p.position_id)) posMap[p.position_id] = p;
            }
          }
        }

        setPositions(posMap);
        setError("");
        setLoading(false);
      } catch (err) {
        console.error("Dashboard load errored:", err);
        setApplications([]);
        setPositions({});
        setError("Could not reach the server.");
        setLoading(false);
      }
    };

    load();
  }, [token]);

  const filtered = applications
    .filter((a) => {
      const matchesStage =
        filter === "All"
          ? a.application_status !== "Withdrawn" &&
            a.application_status !== "Archived"
          : a.application_status === filter;

      const positionTitle = positions[a.position_id]?.title || "";
      const companyName = positions[a.position_id]?.company_name || "";
      const query = search.toLowerCase().trim();

      const matchesSearch =
        query === "" ||
        positionTitle.toLowerCase().includes(query) ||
        companyName.toLowerCase().includes(query);

      return matchesStage && matchesSearch;
    })
    .sort((a, b) => b.job_id - a.job_id);

  const handleDeleteApplication = async () => {
    if (!deleteTarget) return;

    try {
      setIsDeleting(true);
      const res = await fetch(
        `${API}/jobs/applications/${deleteTarget.job_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ application_status: "Withdrawn" }),
        }
      );
      if (res.ok) {
        setApplications((prev) =>
          prev.map((a) =>
            a.job_id === deleteTarget.job_id
              ? { ...a, application_status: "Withdrawn" }
              : a
          )
        );
      }
      setDeleteTarget(null);
    } catch (err) {
      console.error("Failed to remove application:", err);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleJobAdded = async (newApp) => {
    // Fetch the position info for the new app so the card renders correctly
    const r = await fetch(`${API}/jobs/positions/${newApp.position_id}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (r.ok) {
      const pos = await r.json();
      setPositions((prev) => ({ ...prev, [newApp.position_id]: pos }));
    }
    setApplications((prev) => [newApp, ...prev]);
  };

  return (
    <div className="applications-page">
      {showAddJob && (
        <AddJobModal
          onClose={() => setShowAddJob(false)}
          onAdded={handleJobAdded}
        />
      )}

      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        title="Delete this application?"
        message={
          deleteTarget
            ? `Are you sure you want to remove the ${
                positions[deleteTarget.position_id]?.title || "selected"
              } application? This action cannot be undone.`
            : ""
        }
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleDeleteApplication}
        isDeleting={isDeleting}
      />

      {showHistory && (
        <HistoryOverlay
          applications={applications}
          positions={positions}
          onClose={() => setShowHistory(false)}
          onRestore={(id, newStage) =>
            setApplications((prev) =>
              prev.map((a) =>
                a.job_id === id ? { ...a, application_status: newStage } : a
              )
            )
          }
        />
      )}

      <div className="app-page-header">
        <h1>My Applications</h1>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="app-history-global-btn"
            style={{ background: "#4f8ef7", color: "#fff", border: "none" }}
            onClick={() => setShowAddJob(true)}
          >
            + Add Job
          </button>
          <button
            className="app-history-global-btn"
            onClick={() => setShowHistory(true)}
          >
            History
          </button>
        </div>
      </div>

      {error && <p className="applications-error">{error}</p>}

      {!loading && !error && (
        <>
          <div className="app-controls">
            <div className="app-search-row">
              <input
                type="text"
                placeholder="Search jobs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="app-search"
              />

              <select
                className="app-filter-dropdown"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="All">Filter: All</option>
                {STAGES.map((s) => (
                  <option key={s} value={s}>
                    {s} (
                    {
                      applications.filter((a) => a.application_status === s)
                        .length
                    }
                    )
                  </option>
                ))}
              </select>

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
                  onStageChange={(id, newStage) =>
                    setApplications((prev) =>
                      prev.map((a) =>
                        a.job_id === id
                          ? { ...a, application_status: newStage }
                          : a
                      )
                    )
                  }
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
