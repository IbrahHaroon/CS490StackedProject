import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import { api } from "../lib/apiClient";
import "./Dashboard.css";

const PIPELINE_STAGES = [
  "Interested",
  "Applied",
  "Interview",
  "Offer",
  "Rejected",
  "Withdrawn",
  "Accepted",
  "Archived",
];

function DeadlineBadge({ deadline, className = "job-card-meta" }) {
  if (!deadline) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dl = new Date(deadline + "T00:00:00");
  const daysLeft = Math.ceil((dl - today) / (1000 * 60 * 60 * 24));
  const expired = daysLeft < 0;
  const urgent = !expired && daysLeft <= 7;
  return (
    <span
      className={className}
      style={{
        color: expired ? "#ef4444" : urgent ? "#f97316" : "#6b7280",
        fontWeight: urgent || expired ? 600 : 400,
      }}
    >
      {expired
        ? `Deadline passed (${deadline})`
        : daysLeft === 0
          ? "Deadline: Today"
          : `Deadline: ${deadline} · ${daysLeft}d left`}
    </span>
  );
}

function DocViewerModal({ doc, onClose }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!doc) return;
    setLoading(true);
    api
      .get(`/documents/${doc.document_id}/content`, {
        caller: "Dashboard.DocViewerModal",
        action: "fetch_document_content",
      })
      .then((r) => r.json())
      .then((data) => setContent(data.content || ""))
      .catch(() => setContent(""))
      .finally(() => setLoading(false));
  }, [doc]);

  if (!doc) return null;

  return (
    <div className="apply-overlay" onClick={onClose}>
      <div
        className="apply-modal"
        style={{ maxWidth: "680px", maxHeight: "80vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="apply-modal-header">
          <div>
            <h3 className="apply-modal-title">{doc.title}</h3>
            <p className="apply-modal-company">{doc.document_type}</p>
          </div>
          <button className="apply-modal-x" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="apply-modal-divider" />
        {loading ? (
          <p style={{ padding: "1rem", color: "#888" }}>Loading…</p>
        ) : (
          <pre
            style={{
              padding: "1rem",
              overflowY: "auto",
              maxHeight: "55vh",
              whiteSpace: "pre-wrap",
              fontSize: "0.8rem",
              color: "#ccc",
              lineHeight: 1.5,
            }}
          >
            {content || "(empty)"}
          </pre>
        )}
        <div className="apply-modal-actions">
          <button className="apply-modal-cancel" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function AddJobModal({ onClose, onCreate }) {
  const [form, setForm] = useState({
    title: "",
    company_name: "",
    location: "",
    source_url: "",
    description: "",
    stage: "Interested",
    application_date: "",
    deadline: "",
    salary: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleField = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    if (submitting) return;
    setError("");
    setSubmitting(true);
    const body = { ...form };
    if (!body.application_date) delete body.application_date;
    if (!body.deadline) delete body.deadline;
    if (!body.salary) delete body.salary;
    if (!body.location) delete body.location;
    if (!body.source_url) delete body.source_url;
    if (!body.description) delete body.description;
    const err = await onCreate(body);
    setSubmitting(false);
    if (err) setError(err);
  };

  return (
    <div className="apply-overlay" onClick={onClose}>
      <div className="apply-modal" onClick={(e) => e.stopPropagation()}>
        <div className="apply-modal-header">
          <h3 className="apply-modal-title">Add Job</h3>
          <button className="apply-modal-x" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="apply-modal-divider" />
        <div className="apply-modal-fields">
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Job Title *</label>
            <input
              className="filter-panel-input"
              name="title"
              value={form.title}
              onChange={handleField}
              placeholder="Software Engineer"
              required
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Company *</label>
            <input
              className="filter-panel-input"
              name="company_name"
              value={form.company_name}
              onChange={handleField}
              placeholder="Acme Corp"
              required
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Location</label>
            <input
              className="filter-panel-input"
              name="location"
              value={form.location}
              onChange={handleField}
              placeholder="Remote · NYC"
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Source URL</label>
            <input
              className="filter-panel-input"
              name="source_url"
              value={form.source_url}
              onChange={handleField}
              placeholder="https://..."
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Stage</label>
            <select
              className="apply-modal-select"
              name="stage"
              value={form.stage}
              onChange={handleField}
            >
              {PIPELINE_STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Application Date</label>
            <input
              className="filter-panel-input"
              type="date"
              name="application_date"
              value={form.application_date}
              onChange={handleField}
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Deadline</label>
            <input
              className="filter-panel-input"
              type="date"
              name="deadline"
              value={form.deadline}
              onChange={handleField}
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Salary</label>
            <input
              className="filter-panel-input"
              type="number"
              name="salary"
              value={form.salary}
              onChange={handleField}
              placeholder="120000"
            />
          </div>
          <div className="apply-modal-field">
            <label className="apply-modal-field-label">Description</label>
            <textarea
              className="filter-panel-input"
              name="description"
              value={form.description}
              onChange={handleField}
              placeholder="Job description (paste from posting)…"
              rows={4}
            />
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
            onClick={handleSubmit}
            disabled={submitting || !form.title || !form.company_name}
          >
            {submitting ? "Saving…" : "Add Job"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddJob, setShowAddJob] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [actionMessage, setActionMessage] = useState("");
  const [expandedJob, setExpandedJob] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [firstName, setFirstName] = useState("");
  const [sortOrder, setSortOrder] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterStage, setFilterStage] = useState("");
  const [filterCompany, setFilterCompany] = useState("");
  const [filterTitle, setFilterTitle] = useState("");
  const [filterMinSalary, setFilterMinSalary] = useState("");
  const [filterMaxSalary, setFilterMaxSalary] = useState("");
  const [viewingDoc, setViewingDoc] = useState(null);

  const jobBoardRef = useRef(null);
  const filterRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const token = localStorage.getItem("token");

  const refreshJobs = async () => {
    const res = await api.get("/jobs/dashboard", {
      caller: "Dashboard.refreshJobs",
      action: "load_jobs",
    });
    if (res.ok) setJobs(await res.json());
  };

  useEffect(() => {
    const fetchAll = async () => {
      try {
        if (!token) {
          setLoading(false);
          return;
        }
        const [jobsRes, docRes, metricsRes, meRes] = await Promise.all([
          api.get("/jobs/dashboard", {
            caller: "Dashboard.fetchAll",
            action: "load_jobs",
          }),
          api.get("/documents/me", {
            caller: "Dashboard.fetchAll",
            action: "load_documents",
          }),
          api.get("/dashboard/metrics", {
            caller: "Dashboard.fetchAll",
            action: "load_metrics",
          }),
          api.get("/profile/me", {
            caller: "Dashboard.fetchAll",
            action: "load_profile",
          }),
        ]);
        if (jobsRes.ok) setJobs(await jobsRes.json());
        if (docRes.ok) setDocuments(await docRes.json());
        if (metricsRes.ok) setMetrics(await metricsRes.json());
        if (meRes.ok) {
          const profile = await meRes.json();
          setFirstName(profile.first_name || "");
        }
      } catch {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [location.pathname, token]);

  // Open a specific job card when navigated here from another page (?job=<job_id>)
  useEffect(() => {
    const jid = searchParams.get("job");
    if (!jid || jobs.length === 0) return;
    const target = jobs.find((j) => String(j.job_id) === jid);
    if (target) {
      setSelectedJob(target);
      setSearchParams({}, { replace: true });
      setTimeout(
        () => jobBoardRef.current?.scrollIntoView({ behavior: "smooth" }),
        100
      );
    }
  }, [searchParams, jobs]);

  const handleCreateJob = async (body) => {
    const res = await api.post("/jobs", body, {
      caller: "Dashboard.handleCreateJob",
      action: "create_job",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to create job.";
    }
    setShowAddJob(false);
    setActionMessage(`Added ${body.title} @ ${body.company_name}`);
    setTimeout(() => setActionMessage(""), 3000);
    await refreshJobs();
    return null;
  };

  const handleGenerateAIDoc = async (docType, job_id) => {
    if (aiGenerating) return;
    setAiGenerating(true);
    try {
      const endpoint =
        docType === "Resume"
          ? "/documents/generate-resume"
          : "/documents/generate-cover-letter";

      const res = await api.post(
        endpoint,
        { job_id },
        {
          caller: "Dashboard.handleGenerateAIDoc",
          action: `generate_ai_${docType.toLowerCase().replace(" ", "_")}`,
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to generate AI ${docType}.`);
      }

      const docRes = await api.get("/documents/me", {
        caller: "Dashboard.handleGenerateAIDoc",
        action: "refresh_documents",
      });
      if (docRes.ok) setDocuments(await docRes.json());

      setActionMessage(`AI ${docType} generated successfully!`);
      setTimeout(() => setActionMessage(""), 3000);
    } catch {
      // handled by api client
    } finally {
      setAiGenerating(false);
    }
  };

  // Map job_id → resume/cover-letter docs linked to that job (via JobDocumentLink, but
  // we don't fetch links inline. Best-effort: filter docs by ai_draft + match via title.)
  // Documents now don't have job_id — links live separately. Until we add a links call
  // here, this is empty; the document itself is shown on the Documents page.
  const jobResumeMap = {};

  const uniqueCompanies = [
    ...new Set(jobs.map((j) => j.company_name).filter(Boolean)),
  ].sort();
  const hasActiveFilters =
    filterStage ||
    filterCompany ||
    filterTitle ||
    filterMinSalary ||
    filterMaxSalary;

  const clearFilters = () => {
    setFilterStage("");
    setFilterCompany("");
    setFilterTitle("");
    setFilterMinSalary("");
    setFilterMaxSalary("");
  };

  let filteredJobs = searchQuery.trim()
    ? jobs.filter((job) => {
        const q = searchQuery.toLowerCase();
        return (
          job.title?.toLowerCase().includes(q) ||
          job.company_name?.toLowerCase().includes(q) ||
          job.location?.toLowerCase().includes(q) ||
          job.stage?.toLowerCase().includes(q)
        );
      })
    : jobs;

  if (filterStage) {
    filteredJobs = filteredJobs.filter((j) => j.stage === filterStage);
  }
  if (filterCompany) {
    filteredJobs = filteredJobs.filter((j) => j.company_name === filterCompany);
  }
  if (filterTitle) {
    const t = filterTitle.toLowerCase();
    filteredJobs = filteredJobs.filter((j) =>
      j.title?.toLowerCase().includes(t)
    );
  }
  if (filterMinSalary) {
    filteredJobs = filteredJobs.filter(
      (j) => j.salary && Number(j.salary) >= Number(filterMinSalary)
    );
  }
  if (filterMaxSalary) {
    filteredJobs = filteredJobs.filter(
      (j) => j.salary && Number(j.salary) <= Number(filterMaxSalary)
    );
  }

  if (sortOrder === "date-asc") {
    filteredJobs = [...filteredJobs].sort(
      (a, b) => new Date(a.created_at) - new Date(b.created_at)
    );
  } else if (sortOrder === "date-desc") {
    filteredJobs = [...filteredJobs].sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
  } else if (sortOrder === "salary-asc") {
    filteredJobs = [...filteredJobs].sort(
      (a, b) => (Number(a.salary) || 0) - (Number(b.salary) || 0)
    );
  } else if (sortOrder === "salary-desc") {
    filteredJobs = [...filteredJobs].sort(
      (a, b) => (Number(b.salary) || 0) - (Number(a.salary) || 0)
    );
  }

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (filterRef.current && !filterRef.current.contains(e.target)) {
        setFilterOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const scrollToJobBoard = () => {
    jobBoardRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const renderActionButtons = (job) => (
    <div className="job-actions-section">
      <div className="job-action-row">
        <button
          className="job-ai-btn job-ai-btn--resume"
          onClick={() => handleGenerateAIDoc("Resume", job.job_id)}
          disabled={aiGenerating}
          title="Generate AI-powered resume tailored to this job"
        >
          {aiGenerating ? "Generating…" : "Generate Resume"}
        </button>
        <button
          className="job-ai-btn job-ai-btn--cover"
          onClick={() => handleGenerateAIDoc("Cover Letter", job.job_id)}
          disabled={aiGenerating}
          title="Generate AI-powered cover letter tailored to this job"
        >
          {aiGenerating ? "Generating…" : "Generate Cover Letter"}
        </button>
        <button
          className="job-ai-btn job-ai-btn--improve"
          onClick={() => navigate("/documents")}
          title="Browse and improve existing documents"
        >
          Document Library
        </button>
      </div>
      <button
        className="apply-btn apply-btn--edit"
        onClick={() => navigate(`/applications?job=${job.job_id}`)}
      >
        Open Job Detail
      </button>
    </div>
  );

  if (!token) {
    return (
      <div className="dashboard">
        <h1 className="dashboard-welcome">Welcome to your Job Tracker</h1>
        <p style={{ color: "#888", padding: "2rem" }}>
          Sign in to track jobs, generate resumes, and manage your pipeline.
        </p>
        <button
          className="apply-btn"
          onClick={() => navigate("/signin")}
          style={{ marginLeft: "2rem" }}
        >
          Sign In
        </button>
      </div>
    );
  }

  if (loading)
    return (
      <div className="dashboard">
        <p style={{ color: "#888", padding: "2rem" }}>Loading…</p>
      </div>
    );

  return (
    <div className="dashboard">
      {showAddJob && (
        <AddJobModal
          onClose={() => setShowAddJob(false)}
          onCreate={handleCreateJob}
        />
      )}
      {viewingDoc && (
        <DocViewerModal doc={viewingDoc} onClose={() => setViewingDoc(null)} />
      )}
      <h1 className="dashboard-welcome">
        Welcome{firstName ? `, ${firstName}` : ""}
      </h1>
      {actionMessage && <p className="apply-success-msg">{actionMessage}</p>}

      {metrics && (
        <div className="metrics-section">
          <div className="metrics-summary">
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {metrics.total_applications}
              </span>
              <span className="metrics-stat-label">Total Jobs</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {metrics.response_rate}%
              </span>
              <span className="metrics-stat-label">Response Rate</span>
            </div>
            <div className="metrics-stat">
              <span className="metrics-stat-value">
                {(metrics.outcome_counts["Offer"] ?? 0) +
                  (metrics.outcome_counts["Accepted"] ?? 0)}
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
        </div>
      )}

      <div className="dashboard-preview-grid">
        <div className="preview-card preview-card-jobs">
          <div className="preview-card-header">
            <h2>Recent Jobs</h2>
            <button className="view-more-btn" onClick={scrollToJobBoard}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {jobs.length === 0 ? (
              <p className="preview-placeholder">No jobs yet — add one!</p>
            ) : (
              [...jobs]
                .sort((a, b) => b.job_id - a.job_id)
                .slice(0, 3)
                .map((job) => (
                  <div key={job.job_id} className="preview-job-item">
                    <div className="preview-job-item-top">
                      <span className="preview-job-company">
                        {job.company_name}
                      </span>
                      <span
                        className={`preview-status-badge preview-status-${job.stage?.toLowerCase()}`}
                      >
                        {job.stage}
                      </span>
                    </div>
                    <span className="preview-job-title">{job.title}</span>
                  </div>
                ))
            )}
          </div>
        </div>

        <div className="preview-card preview-card-apps">
          <div className="preview-card-header">
            <h2>Applications</h2>
            <button
              className="view-more-btn"
              onClick={() => navigate("/applications")}
            >
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {jobs.filter((j) => j.stage !== "Interested").length === 0 ? (
              <p className="preview-placeholder">No active applications.</p>
            ) : (
              [...jobs]
                .filter((j) => j.stage !== "Interested")
                .sort((a, b) => b.job_id - a.job_id)
                .slice(0, 3)
                .map((job) => (
                  <div key={job.job_id} className="preview-job-item">
                    <div className="preview-job-item-top">
                      <span className="preview-job-company">
                        {job.company_name}
                      </span>
                      <span
                        className={`preview-status-badge preview-status-${job.stage?.toLowerCase()}`}
                      >
                        {job.stage}
                      </span>
                    </div>
                    <span className="preview-job-title">{job.title}</span>
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
                <div key={doc.document_id} className="preview-job-item">
                  <span className="preview-job-company">
                    {doc.document_type}
                  </span>
                  <span className="preview-job-title">{doc.title}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="job-board-search-row">
        <input
          className="job-board-search"
          type="text"
          placeholder="Search by title, company, location, or stage…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <div className="job-board-controls">
          <button
            className="apply-btn apply-btn--row"
            onClick={() => setShowAddJob(true)}
          >
            + Add Job
          </button>
          <div className="job-board-filter-wrap" ref={filterRef}>
            <button
              className={`job-board-control-btn${hasActiveFilters ? " job-board-control-btn--active" : ""}`}
              onClick={() => setFilterOpen((o) => !o)}
            >
              Filter{hasActiveFilters ? " ●" : ""} ▾
            </button>
            {filterOpen && (
              <div className="job-board-filter-panel">
                <div className="filter-panel-row">
                  <label className="filter-panel-label">Stage</label>
                  <select
                    className="filter-panel-select"
                    value={filterStage}
                    onChange={(e) => setFilterStage(e.target.value)}
                  >
                    <option value="">All</option>
                    {PIPELINE_STAGES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filter-panel-row">
                  <label className="filter-panel-label">Company</label>
                  <select
                    className="filter-panel-select"
                    value={filterCompany}
                    onChange={(e) => setFilterCompany(e.target.value)}
                  >
                    <option value="">All</option>
                    {uniqueCompanies.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filter-panel-row">
                  <label className="filter-panel-label">Title</label>
                  <input
                    className="filter-panel-input"
                    type="text"
                    placeholder="Any title"
                    value={filterTitle}
                    onChange={(e) => setFilterTitle(e.target.value)}
                  />
                </div>
                <div className="filter-panel-row">
                  <label className="filter-panel-label">Min Salary</label>
                  <input
                    className="filter-panel-input"
                    type="number"
                    placeholder="e.g. 50000"
                    value={filterMinSalary}
                    onChange={(e) => setFilterMinSalary(e.target.value)}
                  />
                </div>
                <div className="filter-panel-row">
                  <label className="filter-panel-label">Max Salary</label>
                  <input
                    className="filter-panel-input"
                    type="number"
                    placeholder="e.g. 150000"
                    value={filterMaxSalary}
                    onChange={(e) => setFilterMaxSalary(e.target.value)}
                  />
                </div>
                {hasActiveFilters && (
                  <button className="filter-clear-btn" onClick={clearFilters}>
                    Clear Filters
                  </button>
                )}
              </div>
            )}
          </div>
          <div className="job-board-sort-wrap">
            <label className="job-board-control-label">Sort:</label>
            <select
              className="job-board-control-select"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            >
              <option value="">Default</option>
              <option value="date-desc">Date: Newest First</option>
              <option value="date-asc">Date: Oldest First</option>
              <option value="salary-desc">Salary: High to Low</option>
              <option value="salary-asc">Salary: Low to High</option>
            </select>
          </div>
        </div>
      </div>

      <div className="job-board" ref={jobBoardRef}>
        {filteredJobs.length === 0 ? (
          <p style={{ color: "#888", padding: "1rem" }}>
            {jobs.length === 0
              ? "No jobs yet. Click + Add Job to start tracking."
              : "No jobs match your search."}
          </p>
        ) : (
          <>
            <div className="job-board-list">
              {filteredJobs.map((job) => (
                <div
                  key={job.job_id}
                  className={`job-card ${
                    selectedJob?.job_id === job.job_id ? "job-card-selected" : ""
                  }`}
                  onClick={() => setSelectedJob(job)}
                >
                  <div className="job-card-top-row">
                    <span className="job-card-company">{job.company_name}</span>
                    <span
                      className={`preview-status-badge preview-status-${job.stage?.toLowerCase()}`}
                    >
                      {job.stage}
                    </span>
                  </div>
                  <h3 className="job-card-title">{job.title}</h3>
                  {job.location && (
                    <span className="job-card-meta">📍 {job.location}</span>
                  )}
                  <span className="job-card-meta">
                    {job.salary
                      ? `$${Number(job.salary).toLocaleString()}`
                      : "Salary not listed"}
                  </span>
                  {job.application_date && (
                    <span className="job-card-meta">
                      Applied: {job.application_date}
                    </span>
                  )}
                  <DeadlineBadge deadline={job.deadline} />
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
                {selectedJob.location && (
                  <p className="job-detail-meta">📍 {selectedJob.location}</p>
                )}
                <p className="job-detail-meta">
                  {selectedJob.salary
                    ? `$${Number(selectedJob.salary).toLocaleString()}`
                    : "Salary not listed"}
                </p>
                {selectedJob.application_date && (
                  <p className="job-detail-meta">
                    Applied: {selectedJob.application_date}
                  </p>
                )}
                {selectedJob.deadline && (
                  <DeadlineBadge
                    deadline={selectedJob.deadline}
                    className="job-detail-meta"
                  />
                )}
                <p className="job-detail-meta">Stage: {selectedJob.stage}</p>
                {selectedJob.source_url && (
                  <p className="job-detail-meta">
                    <a
                      href={selectedJob.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Original posting ↗
                    </a>
                  </p>
                )}

                {selectedJob.description && (
                  <div className="job-detail-section">
                    <h3>Job Description</h3>
                    <p>{selectedJob.description}</p>
                  </div>
                )}
                {selectedJob.notes && (
                  <div className="job-detail-section">
                    <h3>Notes</h3>
                    <p>{selectedJob.notes}</p>
                  </div>
                )}
                {selectedJob.outcome_notes && (
                  <div className="job-detail-section">
                    <h3>Outcome</h3>
                    <p>{selectedJob.outcome_notes}</p>
                  </div>
                )}

                {renderActionButtons(selectedJob)}
              </div>
            )}

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
                  {selectedJob.location && (
                    <p className="job-detail-meta">📍 {selectedJob.location}</p>
                  )}
                  <p className="job-detail-meta">
                    {selectedJob.salary
                      ? `$${Number(selectedJob.salary).toLocaleString()}`
                      : "Salary not listed"}
                  </p>
                  {selectedJob.deadline && (
                    <DeadlineBadge
                      deadline={selectedJob.deadline}
                      className="job-detail-meta"
                    />
                  )}
                  {selectedJob.description && (
                    <div className="job-detail-section">
                      <h3>Job Description</h3>
                      <p>{selectedJob.description}</p>
                    </div>
                  )}
                  {selectedJob.notes && (
                    <div className="job-detail-section">
                      <h3>Notes</h3>
                      <p>{selectedJob.notes}</p>
                    </div>
                  )}
                  {renderActionButtons(selectedJob)}
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
