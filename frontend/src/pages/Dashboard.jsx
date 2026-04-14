import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Dashboard.css";

const API = "http://localhost:8000";

function ApplyModal({
  job,
  documents,
  onClose,
  onConfirm,
  onGenerateAIDoc,
  aiGenerating,
}) {
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
              <button
                type="button"
                className="generate-ai-doc-btn"
                onClick={() =>
                  onGenerateAIDoc("Resume", job.position_id, setSelectedResume)
                }
                disabled={submitting || aiGenerating}
              >
                Generate AI Resume
              </button>
            </label>
            <select
              className="apply-modal-select"
              value={selectedResume}
              onChange={(e) => setSelectedResume(e.target.value)}
              disabled={submitting || aiGenerating}
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
              <button
                type="button"
                className="generate-ai-doc-btn"
                onClick={() =>
                  onGenerateAIDoc(
                    "Cover Letter",
                    job.position_id,
                    setSelectedCoverLetter
                  )
                }
                disabled={submitting || aiGenerating}
              >
                Generate AI Cover Letter
              </button>
            </label>
            <select
              className="apply-modal-select"
              value={selectedCoverLetter}
              onChange={(e) => setSelectedCoverLetter(e.target.value)}
              disabled={submitting || aiGenerating}
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
  const [aiGenerating, setAiGenerating] = useState(false);
  const [applySuccess, setApplySuccess] = useState("");
  const [expandedJob, setExpandedJob] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

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

  const handleGenerateAIDoc = async (docType, position_id, setSelectedDoc) => {
    if (aiGenerating) return;
    setAiGenerating(true);
    try {
      const endpoint =
        docType === "Resume"
          ? `${API}/documents/generate-resume`
          : `${API}/documents/generate-cover-letter`;

      const body = { position_id };
      // If the user has existing instructions, they could be added here.
      // For now, we'll send a basic request.

      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to generate AI ${docType}.`);
      }

      const newDoc = await res.json();
      // Update the documents list and select the new document
      setDocuments((prevDocs) => [
        ...prevDocs,
        {
          doc_id: newDoc.doc_id,
          document_type: docType,
          document_name: newDoc.document_name,
          document_location: null, // AI generated docs are content-based
          content: newDoc.content,
          user_id: newDoc.user_id,
        },
      ]);
      setSelectedDoc(newDoc.doc_id);
      // Optionally show a success message
      setApplySuccess(`AI ${docType} generated successfully!`);
      setTimeout(() => setApplySuccess(""), 3000);
    } catch (err) {
      console.error(`Error generating AI ${docType}:`, err);
      // Display error in the modal
      // This would require passing a setter for error to ApplyModal
    } finally {
      setAiGenerating(false);
    }
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
            onClick={() => setApplyTarget(job)}
            title="Generate AI-powered resume tailored to this job"
          >
            Generate Resume
          </button>
          <button
            className="job-ai-btn job-ai-btn--cover"
            onClick={() => setApplyTarget(job)}
            title="Generate AI-powered cover letter tailored to this job"
          >
            Generate Cover Letter
          </button>
          <button
            className="job-ai-btn job-ai-btn--improve"
            onClick={() => navigate("/documents")}
            title="Improve existing resume or cover letter"
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
          onGenerateAIDoc={handleGenerateAIDoc}
          aiGenerating={aiGenerating}
        />
      )}
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
                  {(job.location || job.location_type) && (
                    <span className="job-card-meta">
                      📍{" "}
                      {[job.location_type, job.location]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  )}
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
                {(selectedJob.location || selectedJob.location_type) && (
                  <p className="job-detail-meta">
                    📍{" "}
                    {[selectedJob.location_type, selectedJob.location]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                )}
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
                  {(selectedJob.location || selectedJob.location_type) && (
                    <p className="job-detail-meta">
                      📍{" "}
                      {[selectedJob.location_type, selectedJob.location]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  )}
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
