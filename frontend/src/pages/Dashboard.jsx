import { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import { api } from "../lib/apiClient";
import "./Dashboard.css";

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

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

function getDeadlineBoxShadow(deadline) {
  if (!deadline) return undefined;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dl = new Date(deadline + "T00:00:00");
  const daysLeft = Math.ceil((dl - today) / (1000 * 60 * 60 * 24));
  return daysLeft < 7 && daysLeft >= 0
    ? "0 0 12px rgba(239, 68, 68, 0.6)"
    : daysLeft < 0
      ? "0 0 12px rgba(239, 68, 68, 0.8)"
      : undefined;
}

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
        role="dialog"
        aria-modal="true"
        aria-labelledby="doc-viewer-title"
      >
        <div className="apply-modal-header">
          <div>
            <h3 className="apply-modal-title" id="doc-viewer-title">
              {doc.title}
            </h3>
            <p className="apply-modal-company">{doc.document_type}</p>
          </div>
          <button
            className="apply-modal-x"
            onClick={onClose}
            aria-label="Close"
          >
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

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [actionMessage, setActionMessage] = useState("");
  const [expandedJob, setExpandedJob] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const searchQuery = useDebounce(searchInput, 200);
  const [firstName, setFirstName] = useState("");
  const [sortOrder, setSortOrder] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterStage, setFilterStage] = useState("");
  const [filterCompany, setFilterCompany] = useState("");
  const [filterTitle, setFilterTitle] = useState("");
  const [filterMinSalary, setFilterMinSalary] = useState("");
  const [filterMaxSalary, setFilterMaxSalary] = useState("");
  const [viewingDoc, setViewingDoc] = useState(null);
  const [jobDocuments, setJobDocuments] = useState([]);
  const [editingJob, setEditingJob] = useState(null);
  const [editFormValues, setEditFormValues] = useState({});
  const [isSavingJob, setIsSavingJob] = useState(false);
  const [genDocType, setGenDocType] = useState(null);
  const [genInstructions, setGenInstructions] = useState("");
  const [isGeneratingDoc, setIsGeneratingDoc] = useState(false);
  const [genJobId, setGenJobId] = useState(null);

  const jobBoardRef = useRef(null);
  const filterRef = useRef(null);
  const timeoutIdsRef = useRef([]);
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

  const fetchJobDocuments = async (jobId) => {
    try {
      const res = await api.get(`/documents/links/by-job/${jobId}/detailed`, {
        caller: "Dashboard.fetchJobDocuments",
        action: "load_job_documents",
      });
      if (res.ok) {
        const links = await res.json();
        setJobDocuments(links);
      }
    } catch {
      setJobDocuments([]);
    }
  };

  const handleSaveJobEdit = async () => {
    if (!editingJob) return;
    setIsSavingJob(true);
    try {
      const res = await api.put(`/jobs/${editingJob.job_id}`, editFormValues, {
        caller: "Dashboard.handleSaveJobEdit",
        action: "update_job",
      });
      if (res.ok) {
        const updatedJob = await res.json();
        setJobs((prev) =>
          prev.map((j) => (j.job_id === editingJob.job_id ? updatedJob : j))
        );
        setSelectedJob(updatedJob);
        setEditingJob(null);
        setActionMessage("Job updated successfully!");
        const id = setTimeout(() => setActionMessage(""), 3000);
        timeoutIdsRef.current.push(id);
      }
    } catch {
      // handled by api client
    } finally {
      setIsSavingJob(false);
    }
  };

  useEffect(() => {
    const fetchAll = async () => {
      try {
        if (!token) {
          setLoading(false);
          return;
        }
        const [jobsRes, docRes, metricsRes, meRes, analyticsRes] =
          await Promise.all([
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
            api.get("/dashboard/analytics", {
              caller: "Dashboard.fetchAll",
              action: "load_analytics",
            }),
          ]);
        if (jobsRes.ok) setJobs(await jobsRes.json());
        if (docRes.ok) setDocuments(await docRes.json());
        if (metricsRes.ok) setMetrics(await metricsRes.json());
        if (meRes.ok) {
          const profile = await meRes.json();
          setFirstName(profile.first_name || "");
        }
        if (analyticsRes.ok) setAnalytics(await analyticsRes.json());
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
      fetchJobDocuments(target.job_id);
      setSearchParams({}, { replace: true });
      const id = setTimeout(
        () => jobBoardRef.current?.scrollIntoView({ behavior: "smooth" }),
        100
      );
      timeoutIdsRef.current.push(id);
    }
  }, [searchParams, jobs]);

  const handleGenerateAIDoc = (docType, job_id) => {
    setGenDocType(docType);
    setGenInstructions("");
    setGenJobId(job_id);
  };

  const handleGenerateDocConfirm = async () => {
    if (!genJobId || !genDocType || isGeneratingDoc) return;
    setIsGeneratingDoc(true);
    try {
      const endpoint =
        genDocType === "Resume"
          ? "/documents/generate-resume"
          : "/documents/generate-cover-letter";

      const res = await api.post(
        endpoint,
        {
          job_id: genJobId,
          instructions: genInstructions || undefined,
        },
        {
          caller: "Dashboard.handleGenerateDocConfirm",
          action: `generate_ai_${genDocType.toLowerCase().replace(" ", "_")}`,
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to generate AI ${genDocType}.`);
      }

      const docRes = await api.get("/documents/me", {
        caller: "Dashboard.handleGenerateDocConfirm",
        action: "refresh_documents",
      });
      if (docRes.ok) setDocuments(await docRes.json());

      setActionMessage(`AI ${genDocType} generated successfully!`);
      const id = setTimeout(() => setActionMessage(""), 3000);
      timeoutIdsRef.current.push(id);
      setGenDocType(null);
      setGenInstructions("");
      setGenJobId(null);
    } catch {
      // handled by api client
    } finally {
      setIsGeneratingDoc(false);
    }
  };

  // Map job_id → resume/cover-letter docs linked to that job (via JobDocumentLink, but
  // we don't fetch links inline. Best-effort: filter docs by ai_draft + match via title.)
  // Documents now don't have job_id — links live separately. Until we add a links call
  // here, this is empty; the document itself is shown on the Documents page.
  const jobResumeMap = {};

  const uniqueCompanies = useMemo(
    () => [...new Set(jobs.map((j) => j.company_name).filter(Boolean))].sort(),
    [jobs]
  );

  const hasActiveFilters = useMemo(
    () =>
      filterStage ||
      filterCompany ||
      filterTitle ||
      filterMinSalary ||
      filterMaxSalary,
    [filterStage, filterCompany, filterTitle, filterMinSalary, filterMaxSalary]
  );

  const clearFilters = () => {
    setFilterStage("");
    setFilterCompany("");
    setFilterTitle("");
    setFilterMinSalary("");
    setFilterMaxSalary("");
  };

  const filteredJobs = useMemo(() => {
    let result = searchQuery.trim()
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
      result = result.filter((j) => j.stage === filterStage);
    }
    if (filterCompany) {
      result = result.filter((j) => j.company_name === filterCompany);
    }
    if (filterTitle) {
      const t = filterTitle.toLowerCase();
      result = result.filter((j) => j.title?.toLowerCase().includes(t));
    }
    if (filterMinSalary) {
      result = result.filter(
        (j) => j.salary && Number(j.salary) >= Number(filterMinSalary)
      );
    }
    if (filterMaxSalary) {
      result = result.filter(
        (j) => j.salary && Number(j.salary) <= Number(filterMaxSalary)
      );
    }

    if (sortOrder === "date-asc") {
      result = [...result].sort(
        (a, b) => new Date(a.created_at) - new Date(b.created_at)
      );
    } else if (sortOrder === "date-desc") {
      result = [...result].sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
    } else if (sortOrder === "salary-asc") {
      result = [...result].sort(
        (a, b) => (Number(a.salary) || 0) - (Number(b.salary) || 0)
      );
    } else if (sortOrder === "salary-desc") {
      result = [...result].sort(
        (a, b) => (Number(b.salary) || 0) - (Number(a.salary) || 0)
      );
    }

    return result;
  }, [
    searchQuery,
    jobs,
    filterStage,
    filterCompany,
    filterTitle,
    filterMinSalary,
    filterMaxSalary,
    sortOrder,
  ]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (filterRef.current && !filterRef.current.contains(e.target)) {
        setFilterOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    return () => {
      timeoutIdsRef.current.forEach((id) => clearTimeout(id));
      timeoutIdsRef.current = [];
    };
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
          {aiGenerating ? "Generating…" : "Generate AI Resume"}
        </button>
        <button
          className="job-ai-btn job-ai-btn--cover"
          onClick={() => handleGenerateAIDoc("Cover Letter", job.job_id)}
          disabled={aiGenerating}
          title="Generate AI-powered cover letter tailored to this job"
        >
          {aiGenerating ? "Generating…" : "Generate AI Cover Letter"}
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

      {analytics && (
        <div className="analytics-section">
          <div className="analytics-panel">
            <h3 className="metrics-heading">Conversion Funnel</h3>
            <div className="analytics-cards">
              <div className="analytics-card">
                <span className="analytics-card-value">
                  {analytics.overall_conversion_rate}%
                </span>
                <span className="analytics-card-label">Overall</span>
              </div>
              {Object.entries(analytics.conversion_funnel).map(
                ([label, rate]) => (
                  <div key={label} className="analytics-card">
                    <span className="analytics-card-value">{rate}%</span>
                    <span className="analytics-card-label">{label}</span>
                  </div>
                )
              )}
            </div>
          </div>

          {Object.keys(analytics.avg_days_in_stage).length > 0 && (
            <div className="analytics-panel">
              <h3 className="metrics-heading">Avg Time in Stage</h3>
              <div className="analytics-cards">
                {Object.entries(analytics.avg_days_in_stage).map(
                  ([stage, days]) => (
                    <div key={stage} className="analytics-card">
                      <span className="analytics-card-value">{days}d</span>
                      <span className="analytics-card-label">{stage}</span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="job-board-search-row">
        <input
          className="job-board-search"
          type="text"
          placeholder="Search by title, company, location, or stage…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          aria-label="Search jobs by title, company, location, or stage"
        />
        <div className="job-board-controls">
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
                    selectedJob?.job_id === job.job_id
                      ? "job-card-selected"
                      : ""
                  }`}
                  onClick={() => {
                    setSelectedJob(job);
                    fetchJobDocuments(job.job_id);
                  }}
                  style={{
                    boxShadow: getDeadlineBoxShadow(job.deadline),
                    transition: "all 0.3s ease",
                  }}
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
                  style={{
                    position: "absolute",
                    top: "0.5rem",
                    left: "0.5rem",
                    fontSize: "0.75rem",
                    padding: "0.25rem 0.5rem",
                  }}
                >
                  &lt; Expand
                </button>
                <button
                  className="expand-btn"
                  onClick={() => {
                    setEditingJob(selectedJob);
                    setEditFormValues({
                      title: selectedJob.title || "",
                      company_name: selectedJob.company_name || "",
                      location: selectedJob.location || "",
                      location_type: selectedJob.location_type || "",
                      salary: selectedJob.salary || "",
                      years_of_experience:
                        selectedJob.years_of_experience || "",
                      description: selectedJob.description || "",
                      notes: selectedJob.notes || "",
                      application_date: selectedJob.application_date || "",
                      deadline: selectedJob.deadline || "",
                      source_url: selectedJob.source_url || "",
                    });
                  }}
                  style={{
                    position: "absolute",
                    top: "0.75rem",
                    right: "0.75rem",
                    left: "auto",
                  }}
                >
                  Edit
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

                {jobDocuments.length > 0 && (
                  <div className="job-detail-section">
                    <h3>Linked Documents</h3>
                    {jobDocuments.map((link) => (
                      <div
                        key={link.link_id}
                        style={{
                          fontSize: "0.85rem",
                          color: "var(--text-muted)",
                          marginBottom: "0.25rem",
                        }}
                      >
                        📄{" "}
                        {link.document_title || `Version #${link.version_id}`}
                        {link.role && (
                          <span
                            style={{
                              marginLeft: "0.5rem",
                              opacity: 0.6,
                              textTransform: "capitalize",
                            }}
                          >
                            ({link.role.replace("_", " ")})
                          </span>
                        )}
                      </div>
                    ))}
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
                  {selectedJob.outcome_notes && (
                    <div className="job-detail-section">
                      <h3>Outcome</h3>
                      <p>{selectedJob.outcome_notes}</p>
                    </div>
                  )}

                  {jobDocuments.length > 0 && (
                    <div className="job-detail-section">
                      <h3>Linked Documents</h3>
                      {jobDocuments.map((link) => (
                        <div
                          key={link.link_id}
                          style={{
                            fontSize: "0.85rem",
                            color: "var(--text-muted)",
                            marginBottom: "0.25rem",
                          }}
                        >
                          📄{" "}
                          {link.document_title || `Version #${link.version_id}`}
                          {link.role && (
                            <span
                              style={{
                                marginLeft: "0.5rem",
                                opacity: 0.6,
                                textTransform: "capitalize",
                              }}
                            >
                              ({link.role.replace("_", " ")})
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {renderActionButtons(selectedJob)}
                </div>
              </div>
            )}

            {editingJob && (
              <div
                className="expand-overlay"
                onClick={() => setEditingJob(null)}
              >
                <div
                  className="expand-modal"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="expand-close-btn"
                    onClick={() => setEditingJob(null)}
                    title="Close"
                  >
                    &times;
                  </button>
                  <h2
                    className="job-detail-title"
                    style={{ marginBottom: "1.5rem" }}
                  >
                    Edit Job
                  </h2>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "1.25rem",
                    }}
                  >
                    <div>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "0.5rem",
                          fontWeight: 600,
                        }}
                      >
                        Job Title
                      </label>
                      <input
                        type="text"
                        value={editFormValues.title}
                        onChange={(e) =>
                          setEditFormValues((prev) => ({
                            ...prev,
                            title: e.target.value,
                          }))
                        }
                        style={{
                          width: "100%",
                          padding: "0.75rem",
                          borderRadius: "6px",
                          border: "1px solid var(--border)",
                          background: "var(--surface-2)",
                          color: "var(--text)",
                          fontSize: "0.95rem",
                          boxSizing: "border-box",
                        }}
                      />
                    </div>
                    <div>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "0.5rem",
                          fontWeight: 600,
                        }}
                      >
                        Company
                      </label>
                      <input
                        type="text"
                        value={editFormValues.company_name}
                        onChange={(e) =>
                          setEditFormValues((prev) => ({
                            ...prev,
                            company_name: e.target.value,
                          }))
                        }
                        style={{
                          width: "100%",
                          padding: "0.75rem",
                          borderRadius: "6px",
                          border: "1px solid var(--border)",
                          background: "var(--surface-2)",
                          color: "var(--text)",
                          fontSize: "0.95rem",
                          boxSizing: "border-box",
                        }}
                      />
                    </div>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "1rem",
                      }}
                    >
                      <div>
                        <label
                          style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontWeight: 600,
                          }}
                        >
                          Location
                        </label>
                        <input
                          type="text"
                          value={editFormValues.location}
                          onChange={(e) =>
                            setEditFormValues((prev) => ({
                              ...prev,
                              location: e.target.value,
                            }))
                          }
                          placeholder="e.g. New York, NY"
                          style={{
                            width: "100%",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border)",
                            background: "var(--surface-2)",
                            color: "var(--text)",
                            fontSize: "0.95rem",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                      <div>
                        <label
                          style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontWeight: 600,
                          }}
                        >
                          Location Type
                        </label>
                        <select
                          value={editFormValues.location_type || ""}
                          onChange={(e) =>
                            setEditFormValues((prev) => ({
                              ...prev,
                              location_type: e.target.value,
                            }))
                          }
                          style={{
                            width: "100%",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border)",
                            background: "var(--surface-2)",
                            color: "var(--text)",
                            fontSize: "0.95rem",
                            boxSizing: "border-box",
                          }}
                        >
                          <option value="">Select...</option>
                          <option value="Remote">Remote</option>
                          <option value="Onsite">Onsite</option>
                          <option value="Hybrid">Hybrid</option>
                        </select>
                      </div>
                    </div>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "1rem",
                      }}
                    >
                      <div>
                        <label
                          style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontWeight: 600,
                          }}
                        >
                          Salary
                        </label>
                        <input
                          type="number"
                          value={editFormValues.salary}
                          onChange={(e) =>
                            setEditFormValues((prev) => ({
                              ...prev,
                              salary: e.target.value,
                            }))
                          }
                          placeholder="e.g. 120000"
                          style={{
                            width: "100%",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border)",
                            background: "var(--surface-2)",
                            color: "var(--text)",
                            fontSize: "0.95rem",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                      <div>
                        <label
                          style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontWeight: 600,
                          }}
                        >
                          Years of Experience Required
                        </label>
                        <input
                          type="number"
                          value={editFormValues.years_of_experience || ""}
                          onChange={(e) =>
                            setEditFormValues((prev) => ({
                              ...prev,
                              years_of_experience: e.target.value,
                            }))
                          }
                          placeholder="e.g. 5"
                          style={{
                            width: "100%",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border)",
                            background: "var(--surface-2)",
                            color: "var(--text)",
                            fontSize: "0.95rem",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                    </div>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "1rem",
                      }}
                    >
                      <div>
                        <label
                          style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontWeight: 600,
                          }}
                        >
                          Application Date
                        </label>
                        <input
                          type="date"
                          value={editFormValues.application_date || ""}
                          onChange={(e) =>
                            setEditFormValues((prev) => ({
                              ...prev,
                              application_date: e.target.value,
                            }))
                          }
                          style={{
                            width: "100%",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border)",
                            background: "var(--surface-2)",
                            color: "var(--text)",
                            fontSize: "0.95rem",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                      <div>
                        <label
                          style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontWeight: 600,
                          }}
                        >
                          Application Deadline
                        </label>
                        <input
                          type="date"
                          value={editFormValues.deadline}
                          onChange={(e) =>
                            setEditFormValues((prev) => ({
                              ...prev,
                              deadline: e.target.value,
                            }))
                          }
                          style={{
                            width: "100%",
                            padding: "0.75rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border)",
                            background: "var(--surface-2)",
                            color: "var(--text)",
                            fontSize: "0.95rem",
                            boxSizing: "border-box",
                          }}
                        />
                      </div>
                    </div>
                    <div>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "0.5rem",
                          fontWeight: 600,
                        }}
                      >
                        Job Description
                      </label>
                      <textarea
                        value={editFormValues.description}
                        onChange={(e) =>
                          setEditFormValues((prev) => ({
                            ...prev,
                            description: e.target.value,
                          }))
                        }
                        rows={4}
                        style={{
                          width: "100%",
                          padding: "0.75rem",
                          borderRadius: "6px",
                          border: "1px solid var(--border)",
                          background: "var(--surface-2)",
                          color: "var(--text)",
                          fontSize: "0.95rem",
                          boxSizing: "border-box",
                          fontFamily: "inherit",
                          resize: "vertical",
                        }}
                      />
                    </div>
                    <div>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "0.5rem",
                          fontWeight: 600,
                        }}
                      >
                        Notes
                      </label>
                      <textarea
                        value={editFormValues.notes}
                        onChange={(e) =>
                          setEditFormValues((prev) => ({
                            ...prev,
                            notes: e.target.value,
                          }))
                        }
                        rows={3}
                        style={{
                          width: "100%",
                          padding: "0.75rem",
                          borderRadius: "6px",
                          border: "1px solid var(--border)",
                          background: "var(--surface-2)",
                          color: "var(--text)",
                          fontSize: "0.95rem",
                          boxSizing: "border-box",
                          fontFamily: "inherit",
                          resize: "vertical",
                        }}
                      />
                    </div>
                    <div>
                      <label
                        style={{
                          display: "block",
                          marginBottom: "0.5rem",
                          fontWeight: 600,
                        }}
                      >
                        Job Posting URL
                      </label>
                      <input
                        type="url"
                        value={editFormValues.source_url}
                        onChange={(e) =>
                          setEditFormValues((prev) => ({
                            ...prev,
                            source_url: e.target.value,
                          }))
                        }
                        style={{
                          width: "100%",
                          padding: "0.75rem",
                          borderRadius: "6px",
                          border: "1px solid var(--border)",
                          background: "var(--surface-2)",
                          color: "var(--text)",
                          fontSize: "0.95rem",
                          boxSizing: "border-box",
                        }}
                      />
                    </div>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: "0.75rem",
                      marginTop: "2rem",
                      justifyContent: "flex-end",
                    }}
                  >
                    <button
                      onClick={() => setEditingJob(null)}
                      style={{
                        padding: "0.75rem 1.5rem",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        background: "var(--surface-2)",
                        color: "var(--text)",
                        cursor: "pointer",
                        fontSize: "0.95rem",
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveJobEdit}
                      disabled={isSavingJob}
                      style={{
                        padding: "0.75rem 1.5rem",
                        borderRadius: "6px",
                        border: "none",
                        background: "#4f8ef7",
                        color: "#fff",
                        cursor: "pointer",
                        fontSize: "0.95rem",
                        opacity: isSavingJob ? 0.6 : 1,
                      }}
                    >
                      {isSavingJob ? "Saving…" : "Save Changes"}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {genDocType &&
              genJobId &&
              (() => {
                const genJob = jobs.find((j) => j.job_id === genJobId);
                return (
                  <div
                    className="apply-overlay"
                    onClick={() => setGenDocType(null)}
                  >
                    <div
                      className="apply-modal"
                      style={{ maxWidth: "680px" }}
                      onClick={(e) => e.stopPropagation()}
                      role="dialog"
                      aria-modal="true"
                      aria-labelledby="gen-doc-title"
                    >
                      <div className="apply-modal-header">
                        <div>
                          <h3 className="apply-modal-title" id="gen-doc-title">
                            Generate AI {genDocType}
                          </h3>
                        </div>
                        <button
                          className="apply-modal-x"
                          onClick={() => setGenDocType(null)}
                          aria-label="Close"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="apply-modal-divider" />
                      <div
                        style={{
                          padding: "1.5rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "1.25rem",
                        }}
                      >
                        <div>
                          <label
                            style={{
                              display: "block",
                              marginBottom: "0.5rem",
                              fontWeight: 600,
                              fontSize: "0.9rem",
                            }}
                          >
                            Target Job
                          </label>
                          <div
                            style={{
                              padding: "0.75rem",
                              borderRadius: "6px",
                              border: "1px solid var(--border)",
                              background: "var(--surface-2)",
                              color: "var(--text)",
                              fontSize: "0.95rem",
                            }}
                          >
                            {genJob
                              ? `${genJob.title} @ ${genJob.company_name} (${genJob.stage})`
                              : "Loading..."}
                          </div>
                        </div>
                        <div>
                          <label
                            style={{
                              display: "block",
                              marginBottom: "0.5rem",
                              fontWeight: 600,
                              fontSize: "0.9rem",
                            }}
                          >
                            Additional Instructions{" "}
                            <span
                              style={{
                                fontWeight: 400,
                                fontSize: "0.85rem",
                                color: "var(--text-muted)",
                              }}
                            >
                              (optional)
                            </span>
                          </label>
                          <textarea
                            value={genInstructions}
                            onChange={(e) => setGenInstructions(e.target.value)}
                            placeholder={
                              genDocType === "Resume"
                                ? "e.g. Emphasize backend experience, target a senior-level role..."
                                : "e.g. Emphasize leadership experience, formal tone..."
                            }
                            rows={4}
                            style={{
                              width: "100%",
                              padding: "0.75rem",
                              borderRadius: "6px",
                              border: "1px solid var(--border)",
                              background: "var(--surface-2)",
                              color: "var(--text)",
                              fontSize: "0.95rem",
                              fontFamily: "inherit",
                              resize: "vertical",
                              boxSizing: "border-box",
                            }}
                          />
                        </div>
                      </div>
                      <div className="apply-modal-actions">
                        <button
                          className="apply-modal-cancel"
                          onClick={() => setGenDocType(null)}
                          disabled={isGeneratingDoc}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleGenerateDocConfirm}
                          disabled={isGeneratingDoc}
                          style={{
                            padding: "0.6rem 1.4rem",
                            borderRadius: "6px",
                            border: "none",
                            background:
                              genDocType === "Resume" ? "#22c55e" : "#a855f7",
                            color: "#fff",
                            fontFamily: "inherit",
                            fontSize: "0.9rem",
                            fontWeight: 600,
                            cursor: isGeneratingDoc ? "not-allowed" : "pointer",
                            opacity: isGeneratingDoc ? 0.6 : 1,
                          }}
                        >
                          {isGeneratingDoc
                            ? "Generating…"
                            : `Generate ${genDocType}`}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })()}
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
