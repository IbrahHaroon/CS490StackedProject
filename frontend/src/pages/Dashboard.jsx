import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Dashboard.css";

const API = "http://localhost:8000";

function ApplyModal({ job, documents, onClose, onConfirm }) {
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [selectedResume, setSelectedResume] = useState("");
  const [selectedCoverLetter, setSelectedCoverLetter] = useState("");
  const [selectedOther, setSelectedOther] = useState("");

  const resumes = documents.filter((d) => d.document_type === "Resume");
  const coverLetters = documents.filter(
    (d) => d.document_type === "Cover Letter"
  );
  const others = documents.filter(
    (d) => d.document_type !== "Resume" && d.document_type !== "Cover Letter"
  );

  const docLabel = (d) => d.document_name || `Document #${d.doc_id}`;

  const handleConfirm = async () => {
    if (submitting) return;
    setError("");
    setSubmitting(true);
    const err = await onConfirm(job.position_id);
    setSubmitting(false);
    if (err) setError(err);
  };

  return (
    <div className="apply-overlay" onClick={onClose}>
      <div className="apply-modal" onClick={(e) => e.stopPropagation()}>
        <div className="apply-modal-header">
          <div>
            <h3 className="apply-modal-title">{job.title}</h3>
            <p className="apply-modal-company">{job.company_name}</p>
          </div>
          <button className="apply-modal-x" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="apply-modal-divider" />

        <div className="apply-modal-fields">
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">
              Choose your resume
            </label>
            <select
              className="apply-modal-select"
              value={selectedResume}
              onChange={(e) => setSelectedResume(e.target.value)}
              disabled={submitting}
            >
              <option value="">— None —</option>
              {resumes.map((d) => (
                <option key={d.doc_id} value={d.doc_id}>
                  {docLabel(d)}
                </option>
              ))}
            </select>
          </div>

          <div className="apply-modal-field">
            <label className="apply-modal-field-label">
              Choose your cover letter
            </label>
            <select
              className="apply-modal-select"
              value={selectedCoverLetter}
              onChange={(e) => setSelectedCoverLetter(e.target.value)}
              disabled={submitting}
            >
              <option value="">— None —</option>
              {coverLetters.map((d) => (
                <option key={d.doc_id} value={d.doc_id}>
                  {docLabel(d)}
                </option>
              ))}
            </select>
          </div>

          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Other documents</label>
            <select
              className="apply-modal-select"
              value={selectedOther}
              onChange={(e) => setSelectedOther(e.target.value)}
              disabled={submitting}
            >
              <option value="">— None —</option>
              {others.map((d) => (
                <option key={d.doc_id} value={d.doc_id}>
                  {docLabel(d)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && <p className="apply-modal-error">{error}</p>}

        <div className="apply-modal-actions">
          <button
            className="apply-modal-cancel"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            className="apply-modal-confirm"
            onClick={handleConfirm}
            disabled={submitting}
          >
            {submitting ? "Applying…" : "Confirm Apply"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applyTarget, setApplyTarget] = useState(null);
  const [applySuccess, setApplySuccess] = useState("");
  const [expandedJob, setExpandedJob] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Shared AI modal state
  const [aiModal, setAiModal] = useState(null); // 'resume' | 'cover-letter' | 'improve' | null
  const [aiInstructions, setAiInstructions] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiContent, setAiContent] = useState("");
  const [aiDocName, setAiDocName] = useState("");
  const [aiError, setAiError] = useState("");
  // Improve-resume specific
  const [improveDocId, setImproveDocId] = useState("");
  const [improveOriginal, setImproveOriginal] = useState("");
  const [improveImproved, setImproveImproved] = useState("");
  const [improveApplying, setImproveApplying] = useState(false);

  const jobBoardRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const posRes = await fetch(`${API}/jobs/positions/`);
        if (posRes.ok) {
          const data = await posRes.json();
          setJobs(data);
          if (data.length > 0) setSelectedJob(data[0]);
        }

        // Applications, documents, and metrics require auth
        if (token) {
          const [appRes, docRes, metricsRes] = await Promise.all([
            fetch(`${API}/jobs/dashboard`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
            fetch(`${API}/documents/me`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
            fetch(`${API}/dashboard/metrics`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
          ]);
          if (appRes.ok) setApplications(await appRes.json());
          if (docRes.ok) setDocuments(await docRes.json());
          if (metricsRes.ok) setMetrics(await metricsRes.json());
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [location.pathname, token]);

  const handleApply = async (position_id) => {
    const meRes = await fetch(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!meRes.ok) return "You must be signed in to apply.";
    const me = await meRes.json();

    const res = await fetch(`${API}/jobs/applications/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        user_id: me.user_id,
        position_id,
        years_of_experience: 0,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Application failed.";
    }

    setApplyTarget(null);
    setApplySuccess(`Applied to ${applyTarget?.title}!`);
    setTimeout(() => setApplySuccess(""), 3000);
    const appRes = await fetch(`${API}/jobs/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (appRes.ok) setApplications(await appRes.json());
    return null;
  };

  const filteredJobs = searchQuery.trim()
    ? jobs.filter((job) => {
        const q = searchQuery.toLowerCase();
        return (
          job.title?.toLowerCase().includes(q) ||
          job.company_name?.toLowerCase().includes(q) ||
          job.location?.toLowerCase().includes(q) ||
          job.location_type?.toLowerCase().includes(q)
        );
      })
    : jobs;

  const scrollToJobBoard = () => {
    jobBoardRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // ── AI Modal helpers ────────────────────────────────────────────────────────

  const openAiModal = (type) => {
    setAiModal(type);
    setAiInstructions("");
    setAiLoading(false);
    setAiContent("");
    setAiDocName("");
    setAiError("");
    setImproveDocId("");
    setImproveOriginal("");
    setImproveImproved("");
  };

  const closeAiModal = () => setAiModal(null);

  const refreshDocs = async () => {
    const docRes = await fetch(`${API}/documents/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (docRes.ok) setDocuments(await docRes.json());
  };

  const handleGenResume = async () => {
    setAiLoading(true);
    setAiError("");
    try {
      const res = await fetch(`${API}/documents/generate-resume`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          position_id: selectedJob?.position_id,
          instructions: aiInstructions,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiError(err.detail || "Resume generation failed.");
        return;
      }
      const data = await res.json();
      setAiContent(data.content);
      setAiDocName(data.document_name);
      refreshDocs();
    } catch {
      setAiError("Request failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleGenCoverLetter = async () => {
    setAiLoading(true);
    setAiError("");
    try {
      const res = await fetch(`${API}/documents/generate-cover-letter`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          position_id: selectedJob?.position_id,
          instructions: aiInstructions,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiError(err.detail || "Cover letter generation failed.");
        return;
      }
      const data = await res.json();
      setAiContent(data.content);
      setAiDocName(data.document_name);
      refreshDocs();
    } catch {
      setAiError("Request failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleImproveResume = async () => {
    if (!improveDocId) {
      setAiError("Please select a resume to improve.");
      return;
    }
    setAiLoading(true);
    setAiError("");
    try {
      const res = await fetch(`${API}/documents/${improveDocId}/ai-rewrite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ instructions: aiInstructions }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiError(err.detail || "Resume improvement failed.");
        return;
      }
      const data = await res.json();
      setImproveOriginal(data.original);
      setImproveImproved(data.improved);
    } catch {
      setAiError("Request failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleImproveApply = async () => {
    setImproveApplying(true);
    setAiError("");
    try {
      const res = await fetch(`${API}/documents/${improveDocId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: improveImproved }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiError(err.detail || "Failed to apply changes.");
        return;
      }
      closeAiModal();
      setApplySuccess("Resume improvements saved!");
      setTimeout(() => setApplySuccess(""), 3000);
    } catch {
      setAiError("Request failed. Please try again.");
    } finally {
      setImproveApplying(false);
    }
  };

  const resumeDocs = documents.filter((d) => d.document_type === "Resume");

  const MODAL_TITLES = {
    resume: "Generate Resume",
    "cover-letter": "Generate Cover Letter",
    improve: "Improve Resume",
  };

  const renderAiModal = () => {
    if (!aiModal) return null;
    const title = MODAL_TITLES[aiModal];
    const isGenerate = aiModal === "resume" || aiModal === "cover-letter";

    return (
      <div className="dash-ai-overlay" onClick={closeAiModal}>
        <div
          className={`dash-ai-modal${aiModal === "improve" && improveOriginal ? " dash-ai-modal--wide" : ""}`}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="dash-ai-header">
            <div>
              <h2 className="dash-ai-title">{title}</h2>
              {selectedJob && (
                <p className="dash-ai-subtitle">
                  {selectedJob.title} @ {selectedJob.company_name}
                </p>
              )}
            </div>
            <button className="dash-ai-close" onClick={closeAiModal}>
              ✕
            </button>
          </div>

          {/* Input area */}
          {isGenerate && !aiContent && !aiLoading && (
            <div className="dash-ai-body">
              <label className="dash-ai-label">
                Additional Instructions{" "}
                <span className="dash-ai-optional">(optional)</span>
              </label>
              <textarea
                className="dash-ai-textarea"
                value={aiInstructions}
                onChange={(e) => setAiInstructions(e.target.value)}
                placeholder={
                  aiModal === "resume"
                    ? "e.g. Emphasize backend experience, keep to one page…"
                    : "e.g. Keep it formal, highlight leadership experience…"
                }
                rows={3}
              />
              {aiError && <p className="dash-ai-error">{aiError}</p>}
            </div>
          )}

          {aiModal === "improve" && !improveOriginal && !aiLoading && (
            <div className="dash-ai-body">
              <label className="dash-ai-label">Select Resume to Improve</label>
              {resumeDocs.length === 0 ? (
                <p className="dash-ai-hint">
                  No resume documents found. Upload one in the Document Library
                  first.
                </p>
              ) : (
                <select
                  className="dash-ai-select"
                  value={improveDocId}
                  onChange={(e) => setImproveDocId(e.target.value)}
                >
                  <option value="">— Choose a resume —</option>
                  {resumeDocs.map((d) => (
                    <option key={d.doc_id} value={d.doc_id}>
                      {d.document_name || `Document #${d.doc_id}`}
                    </option>
                  ))}
                </select>
              )}
              <label className="dash-ai-label" style={{ marginTop: "0.75rem" }}>
                Instructions{" "}
                <span className="dash-ai-optional">(optional)</span>
              </label>
              <textarea
                className="dash-ai-textarea"
                value={aiInstructions}
                onChange={(e) => setAiInstructions(e.target.value)}
                placeholder="e.g. Tailor for this role, strengthen action verbs…"
                rows={3}
              />
              {aiError && <p className="dash-ai-error">{aiError}</p>}
            </div>
          )}

          {/* Loading spinner */}
          {aiLoading && (
            <div className="dash-ai-loading">
              <div className="dash-ai-spinner" />
              <p>Generating…</p>
            </div>
          )}

          {/* Generate result */}
          {isGenerate && aiContent && !aiLoading && (
            <div className="dash-ai-result">
              <div className="dash-ai-result-header">
                <span className="dash-ai-saved-badge">
                  Saved as &ldquo;{aiDocName}&rdquo; in your Document Library
                </span>
              </div>
              <textarea
                className="dash-ai-result-text"
                value={aiContent}
                readOnly
              />
            </div>
          )}

          {/* Improve result — side-by-side */}
          {aiModal === "improve" && improveOriginal && !aiLoading && (
            <div className="dash-ai-compare">
              <div className="dash-ai-col">
                <div className="dash-ai-col-header">Original</div>
                <pre className="dash-ai-col-text">{improveOriginal}</pre>
              </div>
              <div className="dash-ai-col">
                <div className="dash-ai-col-header dash-ai-col-header--improved">
                  AI Suggestion
                </div>
                <textarea
                  className="dash-ai-col-text dash-ai-col-text--edit"
                  value={improveImproved}
                  onChange={(e) => setImproveImproved(e.target.value)}
                />
              </div>
            </div>
          )}

          {aiError && improveOriginal && (
            <p className="dash-ai-error dash-ai-error--inline">{aiError}</p>
          )}

          {/* Actions */}
          <div className="dash-ai-actions">
            <button className="dash-ai-cancel-btn" onClick={closeAiModal}>
              {aiContent || improveOriginal ? "Close" : "Cancel"}
            </button>
            {isGenerate && !aiContent && !aiLoading && (
              <button
                className={`dash-ai-generate-btn dash-ai-generate-btn--${aiModal}`}
                onClick={
                  aiModal === "resume" ? handleGenResume : handleGenCoverLetter
                }
              >
                {title}
              </button>
            )}
            {aiModal === "improve" && !improveOriginal && !aiLoading && (
              <button
                className="dash-ai-generate-btn dash-ai-generate-btn--improve"
                onClick={handleImproveResume}
                disabled={!improveDocId || resumeDocs.length === 0}
              >
                Generate Improvements
              </button>
            )}
            {aiModal === "improve" && improveOriginal && (
              <>
                <button
                  className="dash-ai-cancel-btn"
                  onClick={() => {
                    setImproveOriginal("");
                    setImproveImproved("");
                    setAiError("");
                  }}
                >
                  Try Again
                </button>
                <button
                  className="dash-ai-save-btn"
                  onClick={handleImproveApply}
                  disabled={improveApplying}
                >
                  {improveApplying ? "Applying…" : "Apply Changes"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  // ── Action buttons row (shared between inline detail and expanded overlay) ──

  const renderActionButtons = (job) => {
    const isApplied = applications.some(
      (a) =>
        a.position_id === job.position_id &&
        a.application_status !== "Withdrawn"
    );
    return (
      <div className="job-actions-section">
        <div className="job-action-row">
          <button
            className="job-ai-btn job-ai-btn--resume"
            onClick={() => openAiModal("resume")}
          >
            Generate Resume
          </button>
          <button
            className="job-ai-btn job-ai-btn--cover"
            onClick={() => openAiModal("cover-letter")}
          >
            Generate Cover Letter
          </button>
          <button
            className="job-ai-btn job-ai-btn--improve"
            onClick={() => openAiModal("improve")}
          >
            Improve Resume
          </button>
          {isApplied ? (
            <button
              className="apply-btn apply-btn-applied apply-btn--row"
              disabled
            >
              Already Applied
            </button>
          ) : (
            <button
              className="apply-btn apply-btn--row"
              onClick={() => setApplyTarget(job)}
            >
              Apply Now
            </button>
          )}
        </div>
        <button
          className="apply-btn apply-btn--edit"
          onClick={() => navigate(`/jobs/edit/${job.position_id}`)}
        >
          Edit Posting
        </button>
      </div>
    );
  };

  if (loading)
    return (
      <div className="dashboard">
        <p style={{ color: "#888", padding: "2rem" }}>Loading…</p>
      </div>
    );

  return (
    <div className="dashboard">
      {applyTarget && (
        <ApplyModal
          job={applyTarget}
          documents={documents}
          onClose={() => setApplyTarget(null)}
          onConfirm={handleApply}
        />
      )}
      {renderAiModal()}

      <h1 className="dashboard-welcome">Welcome</h1>
      {applySuccess && <p className="apply-success-msg">{applySuccess}</p>}

      {token && metrics && (
        <div className="metrics-section">
          <div className="metrics-summary">
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {metrics.total_applications}
              </span>
              <span className="metrics-stat-label">Total Applications</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {metrics.response_rate}%
              </span>
              <span className="metrics-stat-label">Response Rate</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {metrics.outcome_counts["Offer"] +
                  metrics.outcome_counts["Accepted"]}
              </span>
              <span className="metrics-stat-label">Offers</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {metrics.stage_counts["Interview"] ?? 0}
              </span>
              <span className="metrics-stat-label">In Interview</span>
            </div>
          </div>

          {Object.values(metrics.stage_counts).some((v) => v > 0) && (
            <div className="metrics-stages">
              <h3 className="metrics-heading">Pipeline Stages</h3>
              <div className="metrics-stage-grid">
                {Object.entries(metrics.stage_counts)
                  .filter(([, count]) => count > 0)
                  .map(([stage, count]) => (
                    <div
                      key={stage}
                      className={`metrics-stage-badge metrics-stage-${stage.toLowerCase()}`}
                    >
                      <span className="metrics-stage-count">{count}</span>
                      <span className="metrics-stage-name">{stage}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {Object.values(metrics.outcome_counts).some((v) => v > 0) && (
            <div className="metrics-outcomes">
              <h3 className="metrics-heading">Outcomes</h3>
              <div className="metrics-stage-grid">
                {Object.entries(metrics.outcome_counts)
                  .filter(([, count]) => count > 0)
                  .map(([state, count]) => (
                    <div
                      key={state}
                      className={`metrics-stage-badge metrics-outcome-${state.toLowerCase()}`}
                    >
                      <span className="metrics-stage-count">{count}</span>
                      <span className="metrics-stage-name">{state}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="dashboard-preview-grid">
        <div className="preview-card preview-card-jobs">
          <div className="preview-card-header">
            <h2>Jobs for You</h2>
            <button className="view-more-btn" onClick={scrollToJobBoard}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {jobs.length === 0 ? (
              <p className="preview-placeholder">No job listings yet.</p>
            ) : (
              jobs.slice(0, 2).map((job) => (
                <div key={job.position_id} className="preview-job-item">
                  <span className="preview-job-company">
                    {job.company_name}
                  </span>
                  <span className="preview-job-title">{job.title}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="preview-card preview-card-apps">
          <div className="preview-card-header">
            <h2>Current Apps</h2>
            <button
              className="view-more-btn"
              onClick={() => navigate("/applications")}
            >
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {applications.length === 0 ? (
              <p className="preview-placeholder">No applications yet.</p>
            ) : (
              applications.slice(0, 2).map((app) => (
                <div key={app.job_id} className="preview-job-item">
                  <span className="preview-job-company">
                    {app.application_status}
                  </span>
                  <span className="preview-job-title">
                    Application #{app.job_id}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="preview-card preview-card-docs">
          <div className="preview-card-header">
            <h2>Documents</h2>
            <button
              className="view-more-btn"
              onClick={() => navigate("/documents")}
            >
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {documents.length === 0 ? (
              <p className="preview-placeholder">No documents yet.</p>
            ) : (
              documents.slice(0, 2).map((doc) => (
                <div key={doc.doc_id} className="preview-job-item">
                  <span className="preview-job-company">
                    {doc.document_type}
                  </span>
                  <span className="preview-job-title">
                    {doc.document_location
                      ? doc.document_location.split("/").pop()
                      : doc.document_name || "Unnamed document"}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Full job board */}
      <div className="job-board-search-row">
        <input
          className="job-board-search"
          type="text"
          placeholder="Search by title, company, or location…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      <div className="job-board" ref={jobBoardRef}>
        {filteredJobs.length === 0 ? (
          <p style={{ color: "#888", padding: "1rem" }}>
            {jobs.length === 0
              ? "No job listings available."
              : "No jobs match your search."}
          </p>
        ) : (
          <>
            <div className="job-board-list">
              {filteredJobs.map((job) => (
                <div
                  key={job.position_id}
                  className={`job-card ${
                    selectedJob?.position_id === job.position_id
                      ? "job-card-selected"
                      : ""
                  }`}
                  onClick={() => setSelectedJob(job)}
                >
                  <span className="job-card-company">{job.company_name}</span>
                  <h3 className="job-card-title">{job.title}</h3>
                  <span className="job-card-meta">
                    {job.salary
                      ? `$${Number(job.salary).toLocaleString()}`
                      : "Salary not listed"}
                  </span>
                  <span className="job-card-meta">{job.listing_date}</span>
                </div>
              ))}
            </div>

            {selectedJob && (
              <div className="job-board-detail">
                <button
                  className="expand-btn"
                  onClick={() => setExpandedJob(true)}
                >
                  &lt; Expand
                </button>
                <h2 className="job-detail-title">
                  {selectedJob.title} @ {selectedJob.company_name}
                </h2>
                <p className="job-detail-meta">
                  {selectedJob.salary
                    ? `$${Number(selectedJob.salary).toLocaleString()}`
                    : "Salary not listed"}
                </p>
                <p className="job-detail-meta">
                  Listed: {selectedJob.listing_date}
                </p>

                {selectedJob.description && (
                  <div className="job-detail-section">
                    <h3>Job Description</h3>
                    <p>{selectedJob.description}</p>
                  </div>
                )}
                {selectedJob.education_req && (
                  <div className="job-detail-section">
                    <h3>Education</h3>
                    <p>{selectedJob.education_req}</p>
                  </div>
                )}
                {selectedJob.experience_req && (
                  <div className="job-detail-section">
                    <h3>Experience</h3>
                    <p>{selectedJob.experience_req}</p>
                  </div>
                )}

                {token ? (
                  renderActionButtons(selectedJob)
                ) : (
                  <button
                    className="apply-btn"
                    onClick={() => navigate("/signin")}
                  >
                    Sign In to Apply
                  </button>
                )}
              </div>
            )}

            {/* Expanded job overlay */}
            {expandedJob && selectedJob && (
              <div
                className="expand-overlay"
                onClick={() => setExpandedJob(false)}
              >
                <div
                  className="expand-modal"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="expand-close-btn"
                    onClick={() => setExpandedJob(false)}
                    title="Minimize"
                  >
                    &times;
                  </button>
                  <h2 className="job-detail-title">
                    {selectedJob.title} @ {selectedJob.company_name}
                  </h2>
                  <p className="job-detail-meta">
                    {selectedJob.salary
                      ? `$${Number(selectedJob.salary).toLocaleString()}`
                      : "Salary not listed"}
                  </p>
                  <p className="job-detail-meta">
                    Listed: {selectedJob.listing_date}
                  </p>

                  {selectedJob.description && (
                    <div className="job-detail-section">
                      <h3>Job Description</h3>
                      <p>{selectedJob.description}</p>
                    </div>
                  )}
                  {selectedJob.education_req && (
                    <div className="job-detail-section">
                      <h3>Education</h3>
                      <p>{selectedJob.education_req}</p>
                    </div>
                  )}
                  {selectedJob.experience_req && (
                    <div className="job-detail-section">
                      <h3>Experience</h3>
                      <p>{selectedJob.experience_req}</p>
                    </div>
                  )}

                  {token ? (
                    renderActionButtons(selectedJob)
                  ) : (
                    <button
                      className="apply-btn"
                      onClick={() => navigate("/signin")}
                    >
                      Sign In to Apply
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
