import { useEffect, useState } from "react";
import "./Applications.css";
import DeleteConfirmModal from "../components/DeleteConfirmModal";
import { api } from "../lib/apiClient";

const STAGES = [
  "Interested",
  "Applied",
  "Interview",
  "Offer",
  "Accepted",
  "Rejected",
  "Archived",
  "Withdrawn",
];

const STATUS_COLOR = {
  Interested: "#4f8ef7",
  Applied: "#a78bfa",
  Interview: "#f59e0b",
  Offer: "#22c55e",
  Accepted: "#22c55e",
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
  const isTerminal = ["Rejected", "Archived", "Withdrawn"].includes(current);
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

function ApplicationCard({ job, onRemove, onStageChange }) {
  const [expanded, setExpanded] = useState(false);
  const [activity, setActivity] = useState(null);
  const [activityLoaded, setActivityLoaded] = useState(false);
  const [updatingStage, setUpdatingStage] = useState(false);
  const [stageError, setStageError] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const [showCoverLetter, setShowCoverLetter] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [genError, setGenError] = useState("");

  // Deadline + notes (v2: column is `notes`, not `recruiter_notes`)
  const [showDetails, setShowDetails] = useState(false);
  const [editingDetails, setEditingDetails] = useState(false);
  const [detailValues, setDetailValues] = useState({
    deadline: job.deadline || "",
    notes: job.notes || "",
  });
  const [detailSaving, setDetailSaving] = useState(false);
  const [detailError, setDetailError] = useState("");

  const [showFollowUps, setShowFollowUps] = useState(false);
  const [followUps, setFollowUps] = useState([]);
  const [followUpsLoaded, setFollowUpsLoaded] = useState(false);
  const [newFollowUp, setNewFollowUp] = useState({
    description: "",
    due_date: "",
  });
  const [addingFollowUp, setAddingFollowUp] = useState(false);
  const [followUpError, setFollowUpError] = useState("");

  const [showInterviews, setShowInterviews] = useState(false);
  const [interviews, setInterviews] = useState([]);
  const [interviewsLoaded, setInterviewsLoaded] = useState(false);
  const [addingInterview, setAddingInterview] = useState(false);
  const [newInterview, setNewInterview] = useState({
    round_type: "",
    scheduled_at: "",
  });
  const [interviewError, setInterviewError] = useState("");

  const [showDocs, setShowDocs] = useState(false);
  const [docLinks, setDocLinks] = useState([]);
  const [docLinksLoaded, setDocLinksLoaded] = useState(false);

  const [showNotes, setShowNotes] = useState(false);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesValue, setNotesValue] = useState(job.outcome_notes || "");
  const [notesSaving, setNotesSaving] = useState(false);
  const [notesError, setNotesError] = useState("");

  const handleStageChange = async (newStage) => {
    if (newStage === job.stage || updatingStage) return;
    const previousStage = job.stage;
    setUpdatingStage(true);
    setStageError("");
    onStageChange(job.job_id, newStage);
    try {
      const res = await api.put(
        `/jobs/${job.job_id}`,
        { stage: newStage },
        {
          caller: "Applications.handleStageChange",
          action: "update_job_stage",
        }
      );
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        setStageError(
          errBody.detail || `Failed to update stage (${res.status}).`
        );
        onStageChange(job.job_id, previousStage);
      } else {
        setActivity(null);
        setActivityLoaded(false);
      }
    } catch {
      setStageError("Could not reach server. Stage change reverted.");
      onStageChange(job.job_id, previousStage);
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
      const res = await api.get(`/jobs/${job.job_id}/activity`, {
        caller: "Applications.loadActivity",
        action: "fetch_job_activity",
      });
      if (res.ok) setActivity(await res.json());
    } catch {
      // handled by api client logging
    }
    setActivityLoaded(true);
    setExpanded(true);
  };

  const generateCoverLetter = async () => {
    setIsGenerating(true);
    setGenError("");
    try {
      const res = await api.post(
        "/documents/generate-cover-letter",
        { job_id: job.job_id },
        {
          caller: "Applications.generateCoverLetter",
          action: "generate_cover_letter",
        }
      );
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

  const saveDetails = async () => {
    setDetailSaving(true);
    setDetailError("");
    try {
      const res = await api.put(
        `/jobs/${job.job_id}`,
        {
          deadline: detailValues.deadline || null,
          notes: detailValues.notes || null,
        },
        {
          caller: "Applications.saveDetails",
          action: "save_deadline_and_notes",
        }
      );
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

  const loadFollowUps = async () => {
    if (!showFollowUps && !followUpsLoaded) {
      try {
        const res = await api.get(`/jobs/${job.job_id}/followups`, {
          caller: "Applications.loadFollowUps",
          action: "fetch_follow_ups",
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
      const res = await api.post(
        `/jobs/${job.job_id}/followups`,
        {
          description: newFollowUp.description,
          due_date: newFollowUp.due_date || null,
        },
        { caller: "Applications.createFollowUp", action: "create_follow_up" }
      );
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
      const res = await api.put(
        `/followups/${fu.followup_id}`,
        { completed: !fu.completed },
        {
          caller: "Applications.toggleComplete",
          action: "toggle_follow_up_complete",
        }
      );
      if (res.ok) {
        const updated = await res.json();
        setFollowUps((prev) =>
          prev.map((f) => (f.followup_id === fu.followup_id ? updated : f))
        );
      }
    } catch {
      // silently fail
    }
  };

  const deleteFollowUp = async (followup_id) => {
    try {
      const res = await api.delete(`/followups/${followup_id}`, {
        caller: "Applications.deleteFollowUp",
        action: "delete_follow_up",
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
        const res = await api.get(`/jobs/${job.job_id}/interviews`, {
          caller: "Applications.loadInterviews",
          action: "fetch_interviews",
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
      const res = await api.post(
        `/jobs/${job.job_id}/interviews`,
        {
          round_type: newInterview.round_type,
          scheduled_at: newInterview.scheduled_at,
        },
        { caller: "Applications.createInterview", action: "create_interview" }
      );
      if (res.ok) {
        const created = await res.json();
        setInterviews((prev) => [...prev, created]);
        setNewInterview({ round_type: "", scheduled_at: "" });
        setInterviewError("");
        setAddingInterview(false);
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
      const res = await api.delete(`/interviews/${interview_id}`, {
        caller: "Applications.deleteInterview",
        action: "delete_interview",
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

  const loadDocLinks = async () => {
    if (!showDocs && !docLinksLoaded) {
      try {
        const res = await api.get(`/documents/links/by-job/${job.job_id}`, {
          caller: "Applications.loadDocLinks",
          action: "fetch_doc_links",
        });
        if (res.ok) setDocLinks(await res.json());
      } catch {
        // leave empty
      }
      setDocLinksLoaded(true);
    }
    setShowDocs((v) => !v);
  };

  const saveNotes = async () => {
    setNotesSaving(true);
    setNotesError("");
    try {
      const res = await api.put(
        `/jobs/${job.job_id}`,
        { outcome_notes: notesValue },
        { caller: "Applications.saveNotes", action: "save_outcome_notes" }
      );
      if (res.ok) {
        setEditingNotes(false);
      } else {
        const errBody = await res.json().catch(() => ({}));
        setNotesError(
          errBody.detail || `Failed to save notes (${res.status}).`
        );
      }
    } catch {
      setNotesError("Failed to save notes.");
    }
    setNotesSaving(false);
  };

  return (
    <div
      className="app-card"
      style={{
        border:
          job.stage === "Interview"
            ? "2px solid orange"
            : job.stage === "Offer" || job.stage === "Accepted"
              ? "2px solid green"
              : "1px solid #333",
        boxShadow: "none",
        transition: "0.2s ease-in-out",
      }}
    >
      <div className="app-card-header">
        <div className="app-card-info">
          <h3 className="app-card-title">{job.title}</h3>
          {job.company_name && (
            <span className="app-card-company">{job.company_name}</span>
          )}
          {job.application_date && (
            <span className="app-card-meta">Applied {job.application_date}</span>
          )}
          {job.years_of_experience !== null &&
            job.years_of_experience !== undefined && (
              <span className="app-card-meta">
                {job.years_of_experience} yr
                {job.years_of_experience !== 1 ? "s" : ""} experience
              </span>
            )}
        </div>

        <div className="app-card-right">
          <select
            className="app-stage-select"
            value={job.stage}
            disabled={updatingStage}
            onChange={(e) => handleStageChange(e.target.value)}
            style={{
              borderColor: STATUS_COLOR[job.stage],
              color: STATUS_COLOR[job.stage],
            }}
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          {stageError && (
            <span
              className="applications-error"
              style={{
                fontSize: "0.75rem",
                maxWidth: "160px",
                textAlign: "right",
              }}
            >
              {stageError}
            </span>
          )}
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

      <Pipeline current={job.stage} />

      {/* Deadline & Notes */}
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
                  <span className="details-label">Notes</span>
                  <span className="details-value">
                    {detailValues.notes || (
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
                <label className="details-label">Contact / Recruiter Notes</label>
                <textarea
                  className="details-textarea"
                  value={detailValues.notes}
                  onChange={(e) =>
                    setDetailValues((prev) => ({
                      ...prev,
                      notes: e.target.value,
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

      {/* Follow-ups */}
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

      {/* Linked Documents */}
      <div className="followup-section">
        <button
          className="app-history-btn followup-toggle"
          onClick={loadDocLinks}
        >
          Documents{docLinks.length > 0 ? ` (${docLinks.length})` : ""}{" "}
          {showDocs ? "▾" : "▸"}
        </button>
        {showDocs && (
          <div className="followup-body">
            {docLinks.length === 0 ? (
              <p className="followup-empty">
                No documents linked to this job yet. Generate a resume or cover
                letter from the Dashboard or Document Library.
              </p>
            ) : (
              <ul className="followup-list">
                {docLinks.map((link) => (
                  <li key={link.link_id} className="followup-item">
                    <span className="followup-desc">
                      Version #{link.version_id}
                    </span>
                    <span className="followup-date">{link.role || "—"}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Outcome Notes */}
      <div className="followup-section">
        <button
          className="app-history-btn followup-toggle"
          onClick={() => setShowNotes((v) => !v)}
        >
          Outcome Notes {showNotes ? "▾" : "▸"}
        </button>
        {showNotes && (
          <div className="followup-body">
            {editingNotes ? (
              <div className="followup-add-form">
                <textarea
                  className="followup-input"
                  rows={4}
                  placeholder="Add your outcome notes here…"
                  value={notesValue}
                  onChange={(e) => setNotesValue(e.target.value)}
                  style={{ resize: "vertical" }}
                />
                {notesError && (
                  <p
                    style={{
                      color: "#ef4444",
                      fontSize: "13px",
                      margin: "4px 0",
                    }}
                  >
                    {notesError}
                  </p>
                )}
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    className="app-history-btn"
                    onClick={saveNotes}
                    disabled={notesSaving}
                  >
                    {notesSaving ? "Saving…" : "Save"}
                  </button>
                  <button
                    className="app-history-btn"
                    onClick={() => {
                      setEditingNotes(false);
                      setNotesValue(job.outcome_notes || "");
                      setNotesError("");
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                {notesValue ? (
                  <p
                    className="followup-desc"
                    style={{ whiteSpace: "pre-wrap" }}
                  >
                    {notesValue}
                  </p>
                ) : (
                  <p className="followup-empty">No outcome notes yet.</p>
                )}
                <button
                  className="app-history-btn"
                  style={{ marginTop: "8px" }}
                  onClick={() => setEditingNotes(true)}
                >
                  {notesValue ? "Edit Notes" : "+ Add Notes"}
                </button>
              </>
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
                const stageLabel = a.to_stage || a.from_stage || "—";
                const dotColor =
                  meta.color || STATUS_COLOR[stageLabel] || "#888";
                return (
                  <li key={a.activity_id} className="app-activity-item">
                    <span
                      className="app-activity-dot"
                      style={{ backgroundColor: dotColor }}
                      title={meta.label || stageLabel}
                    >
                      {meta.icon !== "●" ? meta.icon : ""}
                    </span>
                    <span className="app-activity-stage">
                      {meta.label
                        ? `${meta.label}: `
                        : a.from_stage
                          ? `${a.from_stage} → `
                          : ""}
                      {stageLabel}
                    </span>
                    {a.notes && (
                      <span className="app-activity-notes">{a.notes}</span>
                    )}
                    <span className="app-activity-date">
                      {new Date(a.occurred_at).toLocaleString()}
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

function HistoryOverlay({ jobs, onClose, onRestore }) {
  const [allActivity, setAllActivity] = useState([]);
  const [activityByJob, setActivityByJob] = useState({});
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [restoringJobId, setRestoringJobId] = useState(null);

  useEffect(() => {
    const loadAll = async () => {
      const results = [];
      const byJob = {};
      await Promise.all(
        jobs.map(async (job) => {
          try {
            const res = await api.get(`/jobs/${job.job_id}/activity`, {
              caller: "Applications.HistoryOverlay",
              action: "fetch_all_activity",
            });
            if (res.ok) {
              const activities = await res.json();
              const title = `${job.title} @ ${job.company_name}`;
              byJob[job.job_id] = activities;
              activities.forEach((a) =>
                results.push({ ...a, jobTitle: title, job_id: job.job_id })
              );
            }
          } catch {
            /* skip */
          }
        })
      );
      results.sort((a, b) => new Date(b.occurred_at) - new Date(a.occurred_at));
      setAllActivity(results);
      setActivityByJob(byJob);
      setLoadingHistory(false);
    };
    loadAll();
  }, [jobs]);

  const currentStageById = Object.fromEntries(
    jobs.map((j) => [j.job_id, j.stage])
  );

  const handleRestore = async (jobId) => {
    setRestoringJobId(jobId);
    const history = activityByJob[jobId] || [];
    const sorted = [...history].sort(
      (a, b) => new Date(b.occurred_at) - new Date(a.occurred_at)
    );
    const previous = sorted.find((h) => {
      const stage = h.to_stage;
      return stage && stage !== "Archived" && stage !== "Withdrawn";
    });
    const targetStage = previous?.to_stage || "Applied";

    try {
      const res = await api.put(
        `/jobs/${jobId}`,
        { stage: targetStage },
        { caller: "Applications.handleRestore", action: "restore_job" }
      );
      if (!res.ok) return;
      onRestore(jobId, targetStage);
    } catch {
      // handled by api client logging
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
        <h2 className="history-modal-title">Job History</h2>

        <h3 className="history-section-title">Activity Timeline</h3>
        {loadingHistory ? (
          <p className="applications-placeholder">Loading history...</p>
        ) : allActivity.length === 0 ? (
          <p className="applications-placeholder">No activity recorded yet.</p>
        ) : (
          <ul className="app-activity-list">
            {allActivity.map((a, i) => {
              const stageLabel = a.to_stage || a.from_stage || "—";
              const isArchivedEntry = stageLabel === "Archived";
              const isWithdrawnEntry = stageLabel === "Withdrawn";
              const isCurrentlyArchived =
                currentStageById[a.job_id] === "Archived";
              const isCurrentlyWithdrawn =
                currentStageById[a.job_id] === "Withdrawn";
              const showRestore =
                (isArchivedEntry && isCurrentlyArchived) ||
                (isWithdrawnEntry && isCurrentlyWithdrawn);
              const meta =
                EVENT_TYPE_META[a.event_type] || EVENT_TYPE_META.stage_change;
              const dotColor =
                meta.color || STATUS_COLOR[stageLabel] || "#888";
              return (
                <li key={`${a.activity_id}-${i}`} className="history-item">
                  <span
                    className="app-activity-dot"
                    style={{ backgroundColor: dotColor }}
                    title={meta.label || stageLabel}
                  >
                    {meta.icon !== "●" ? meta.icon : ""}
                  </span>
                  <span className="history-job-title">{a.jobTitle}</span>
                  <span className="app-activity-stage">
                    {meta.label ? `${meta.label}: ` : ""}
                    {stageLabel}
                  </span>
                  {a.notes && (
                    <span className="app-activity-notes">{a.notes}</span>
                  )}
                  <span className="app-activity-date">
                    {new Date(a.occurred_at).toLocaleString()}
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
    stage: "Interested",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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
        stage: form.stage,
      };
      const res = await api.post("/jobs", body, {
        caller: "Applications.AddJobModal",
        action: "create_job",
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        setError(detail.detail || "Failed to save job.");
        return;
      }
      const newJob = await res.json();
      onAdded(newJob);
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
            <label className="details-label">Initial Stage</label>
            <select
              className="app-stage-select"
              style={{ width: "100%", boxSizing: "border-box" }}
              value={form.stage}
              onChange={(e) => setForm((p) => ({ ...p, stage: e.target.value }))}
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
  const [jobs, setJobs] = useState([]);
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
        const res = await api.get("/jobs/dashboard", {
          caller: "Applications.load",
          action: "fetch_dashboard",
        });

        if (!res.ok) {
          setJobs([]);
          setError("Could not load jobs. Please sign in again.");
          setLoading(false);
          return;
        }

        setJobs(await res.json());
        setError("");
        setLoading(false);
      } catch {
        setJobs([]);
        setError("Could not reach the server.");
        setLoading(false);
      }
    };

    load();
  }, [token]);

  const filtered = jobs
    .filter((j) => {
      const matchesStage =
        filter === "All"
          ? j.stage !== "Withdrawn" && j.stage !== "Archived"
          : j.stage === filter;

      const query = search.toLowerCase().trim();
      const matchesSearch =
        query === "" ||
        (j.title || "").toLowerCase().includes(query) ||
        (j.company_name || "").toLowerCase().includes(query);

      return matchesStage && matchesSearch;
    })
    .sort((a, b) => b.job_id - a.job_id);

  const handleDeleteApplication = async () => {
    if (!deleteTarget) return;
    try {
      setIsDeleting(true);
      const res = await api.put(
        `/jobs/${deleteTarget.job_id}`,
        { stage: "Withdrawn" },
        {
          caller: "Applications.handleDeleteApplication",
          action: "withdraw_job",
        }
      );
      if (res.ok) {
        setJobs((prev) =>
          prev.map((j) =>
            j.job_id === deleteTarget.job_id ? { ...j, stage: "Withdrawn" } : j
          )
        );
      }
      setDeleteTarget(null);
    } catch {
      // handled by api client logging
    } finally {
      setIsDeleting(false);
    }
  };

  const handleJobAdded = (newJob) => {
    setJobs((prev) => [newJob, ...prev]);
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
        title="Withdraw this job?"
        message={
          deleteTarget
            ? `Mark "${deleteTarget.title} @ ${deleteTarget.company_name}" as Withdrawn? You can restore it later from History.`
            : ""
        }
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleDeleteApplication}
        isDeleting={isDeleting}
      />

      {showHistory && (
        <HistoryOverlay
          jobs={jobs}
          onClose={() => setShowHistory(false)}
          onRestore={(id, newStage) =>
            setJobs((prev) =>
              prev.map((j) => (j.job_id === id ? { ...j, stage: newStage } : j))
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
                    {s} ({jobs.filter((j) => j.stage === s).length})
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
                ? "No jobs yet."
                : `No jobs with status "${filter}".`}
            </p>
          ) : (
            <div className="app-list">
              {filtered.map((job) => (
                <ApplicationCard
                  key={job.job_id}
                  job={job}
                  onRemove={() => setDeleteTarget(job)}
                  onStageChange={(id, newStage) =>
                    setJobs((prev) =>
                      prev.map((j) =>
                        j.job_id === id ? { ...j, stage: newStage } : j
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
