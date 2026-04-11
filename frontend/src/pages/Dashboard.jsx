import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Dashboard.css";

const API = "http://localhost:8000";

const STAGE_COLORS = {
  Interested: "#4f8ef7",
  Applied: "#a78bfa",
  Interview: "#f59e0b",
  Offer: "#22c55e",
  Rejected: "#ef4444",
  Archived: "#6b7280",
  Withdrawn: "#374151",
};

const LOCATION_FILTER_TYPES = ["All", "Remote", "Hybrid", "On-site", "In-Person"];

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

function MetricsBar({ metrics }) {
  if (!metrics) return null;

  const stages = ["Interested", "Applied", "Interview", "Offer", "Rejected"];

  return (
    <div className="metrics-bar">
      <div className="metric-card">
        <span className="metric-value">{metrics.total}</span>
        <span className="metric-label">Total Applications</span>
      </div>
      {stages.map((s) => {
        const count = metrics.by_stage?.[s] ?? 0;
        if (count === 0) return null;
        return (
          <div className="metric-card" key={s}>
            <span className="metric-value" style={{ color: STAGE_COLORS[s] }}>
              {count}
            </span>
            <span className="metric-label">{s}</span>
          </div>
        );
      })}
      {metrics.awaiting_response > 0 && (
        <div className="metric-card">
          <span className="metric-value" style={{ color: "#f59e0b" }}>
            {metrics.awaiting_response}
          </span>
          <span className="metric-label">Awaiting Response</span>
        </div>
      )}
      <div className="metric-card metric-card-rate">
        <span className="metric-value">{metrics.response_rate}%</span>
        <span className="metric-label">Response Rate</span>
      </div>
    </div>
  );
}

function ApplyModal({ job, onClose, onConfirm }) {
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleConfirm = async () => {
    if (submitting) return;
    setError("");
    setSubmitting(true);
    const err = await onConfirm(job.position_id);
    setSubmitting(false);
    if (err) setError(err);
  };

  return (
    <div className="apply-overlay">
      <div className="apply-modal">
        <h3 className="apply-modal-title">Apply for {job.title}</h3>
        <p className="apply-modal-company">{job.company_name}</p>
        <p className="apply-modal-company">Are you sure you want to apply?</p>
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

function JobDetailPanel({ job, applications, token, onApply, onEdit }) {
  const [activity, setActivity] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const appliedApp = applications.find(
    (a) =>
      a.position_id === job.position_id &&
      a.application_status !== "Withdrawn"
  );
  const alreadyApplied = !!appliedApp;

  // Reset history when switching jobs
  useEffect(() => {
    setActivity(null);
    setShowHistory(false);
  }, [job.position_id]);

  const toggleHistory = async () => {
    if (showHistory) {
      setShowHistory(false);
      return;
    }
    if (activity) {
      setShowHistory(true);
      return;
    }
    if (!appliedApp) return;
    setLoadingHistory(true);
    try {
      const res = await fetch(
        `${API}/jobs/applications/${appliedApp.job_id}/activity`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) setActivity(await res.json());
    } catch (err) {
      console.error("Failed to load activity:", err);
    }
    setLoadingHistory(false);
    setShowHistory(true);
  };

  return (
    <div className="job-board-detail">
      <h2 className="job-detail-title">
        {job.title}
        <span className="job-detail-company"> @ {job.company_name}</span>
      </h2>

      <div className="job-detail-meta-row">
        {job.salary && (
          <span className="job-detail-chip job-detail-chip-salary">
            ${Number(job.salary).toLocaleString()}
          </span>
        )}
        {job.location_type && (
          <span className="job-detail-chip">{job.location_type}</span>
        )}
        {job.location && (
          <span className="job-detail-chip">{job.location}</span>
        )}
        <span className="job-detail-chip">Listed {job.listing_date}</span>
      </div>

      {/* My Application status + stage history */}
      {token && alreadyApplied && (
        <div className="job-detail-app-status">
          <div className="job-detail-app-status-row">
            <span className="job-detail-app-label">My Application</span>
            <span
              className="job-detail-app-badge"
              style={{
                color: STAGE_COLORS[appliedApp.application_status],
                borderColor: STAGE_COLORS[appliedApp.application_status] + "55",
                backgroundColor:
                  STAGE_COLORS[appliedApp.application_status] + "18",
              }}
            >
              {appliedApp.application_status}
            </span>
            {appliedApp.stage_changed_at && (
              <span className="job-detail-app-time">
                Updated {timeAgo(appliedApp.stage_changed_at)}
              </span>
            )}
          </div>
          <button
            className="job-detail-history-btn"
            onClick={toggleHistory}
            disabled={loadingHistory}
          >
            {loadingHistory
              ? "Loading…"
              : showHistory
              ? "Hide Stage History ▲"
              : "View Stage History ▼"}
          </button>
          {showHistory && activity && (
            <div className="job-detail-activity">
              {activity.map((a) => (
                <div key={a.activity_id} className="job-detail-activity-item">
                  <span
                    className="job-detail-activity-dot"
                    style={{
                      backgroundColor: STAGE_COLORS[a.stage] || "#888",
                    }}
                  />
                  <span className="job-detail-activity-stage">{a.stage}</span>
                  <span className="job-detail-activity-date">
                    {new Date(a.changed_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {job.description && (
        <div className="job-detail-section">
          <h3>Job Description</h3>
          <p>{job.description}</p>
        </div>
      )}
      {job.education_req && (
        <div className="job-detail-section">
          <h3>Education Requirements</h3>
          <p>{job.education_req}</p>
        </div>
      )}
      {job.experience_req && (
        <div className="job-detail-section">
          <h3>Experience Requirements</h3>
          <p>{job.experience_req}</p>
        </div>
      )}

      {token ? (
        <div className="job-detail-actions">
          {alreadyApplied ? (
            <button className="apply-btn apply-btn-applied" disabled>
              Already Applied
            </button>
          ) : (
            <button className="apply-btn" onClick={onApply}>
              Apply Now
            </button>
          )}
          <button
            className="apply-btn apply-btn-secondary"
            onClick={onEdit}
          >
            Edit Posting
          </button>
        </div>
      ) : (
        <div className="job-detail-actions">
          <button className="apply-btn" onClick={() => onEdit("signin")}>
            Sign In to Apply
          </button>
        </div>
      )}
    </div>
  );
}

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [filteredJobs, setFilteredJobs] = useState([]);
  const [search, setSearch] = useState("");
  const [locationFilter, setLocationFilter] = useState("All");
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [careerPrefs, setCareerPrefs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applyTarget, setApplyTarget] = useState(null);
  const [applySuccess, setApplySuccess] = useState("");
  const [expandedJob, setExpandedJob] = useState(false);
  const jobBoardRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchAll = async () => {
      try {
        // Positions are public — no auth needed
        const posRes = await fetch(`${API}/jobs/positions/`);
        if (posRes.ok) {
          const data = await posRes.json();
          setJobs(data);
          if (data.length > 0) setSelectedJob(data[0]);
        }

        // Applications and documents require auth
        if (token) {
          const [appRes, docRes] = await Promise.all([
            fetch(`${API}/jobs/dashboard`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
            fetch(`${API}/documents/me`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
          ]);
          if (appRes.ok) setApplications(await appRes.json());
          if (docRes.ok) setDocuments(await docRes.json());
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

    const [appRes, metricsRes] = await Promise.all([
      fetch(`${API}/jobs/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`${API}/dashboard/metrics`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ]);
    if (appRes.ok) setApplications(await appRes.json());
    if (metricsRes.ok) setMetrics(await metricsRes.json());
    return null;
  };

  const scrollToJobBoard = () => {
    jobBoardRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const hasPrefs =
    careerPrefs &&
    (careerPrefs.target_roles ||
      careerPrefs.work_mode ||
      careerPrefs.salary_preference ||
      careerPrefs.location_preferences);

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
          onClose={() => setApplyTarget(null)}
          onConfirm={handleApply}
        />
      )}

      <h1 className="dashboard-welcome">Welcome</h1>
      {applySuccess && <p className="apply-success-msg">{applySuccess}</p>}

      {/* Dashboard metrics */}
      {token && metrics && <MetricsBar metrics={metrics} />}

      {/* Preview grid */}
      <div className="dashboard-preview-grid">
        {/* Jobs preview — spans all right-column rows */}
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
              jobs.slice(0, 3).map((job) => (
                <div key={job.position_id} className="preview-job-item">
                  <span className="preview-job-company">
                    {job.company_name}
                  </span>
                  <span className="preview-job-title">{job.title}</span>
                  {job.location_type && (
                    <span className="preview-job-badge">{job.location_type}</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Current applications */}
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

        {/* Documents */}
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

        {/* Career Preferences */}
        <div className="preview-card preview-card-prefs">
          <div className="preview-card-header">
            <h2>Career Preferences</h2>
            {token && (
              <button
                className="view-more-btn"
                onClick={() => navigate("/career-preferences")}
              >
                Edit →
              </button>
            )}
          </div>
          <div className="preview-card-body">
            {!token ? (
              <p className="preview-placeholder">Sign in to set preferences.</p>
            ) : !hasPrefs ? (
              <div className="pref-empty">
                <p className="preview-placeholder">No preferences set yet.</p>
                <button
                  className="pref-set-link"
                  onClick={() => navigate("/career-preferences")}
                >
                  Set preferences →
                </button>
              </div>
            ) : (
              <>
                {careerPrefs.target_roles && (
                  <div className="pref-item">
                    <span className="pref-label">Roles</span>
                    <span className="pref-value">{careerPrefs.target_roles}</span>
                  </div>
                )}
                {careerPrefs.work_mode && (
                  <div className="pref-item">
                    <span className="pref-label">Work Mode</span>
                    <span className="pref-value">{careerPrefs.work_mode}</span>
                  </div>
                )}
                {careerPrefs.salary_preference && (
                  <div className="pref-item">
                    <span className="pref-label">Salary</span>
                    <span className="pref-value">
                      {careerPrefs.salary_preference}
                    </span>
                  </div>
                )}
                {careerPrefs.location_preferences && (
                  <div className="pref-item">
                    <span className="pref-label">Locations</span>
                    <span className="pref-value">
                      {careerPrefs.location_preferences}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Full job board */}
      <div className="job-board" ref={jobBoardRef}>
        {jobs.length === 0 ? (
          <p style={{ color: "#888", padding: "1rem" }}>
            No job listings available.
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
                  <div className="job-card-chips">
                    {job.location_type && (
                      <span className="job-card-chip">{job.location_type}</span>
                    )}
                    {job.location && (
                      <span className="job-card-chip">{job.location}</span>
                    )}
                  </div>
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
                {token &&
                  (applications.some(
                    (a) =>
                      a.position_id === selectedJob.position_id &&
                      a.application_status !== "Withdrawn"
                  ) ? (
                    <button className="apply-btn apply-btn-applied" disabled>
                      Already Applied
                    </button>
                  ) : (
                    <button
                      className="apply-btn"
                      style={{ backgroundColor: "#6c757d" }}
                      onClick={() =>
                        navigate(`/jobs/edit/${selectedJob.position_id}`)
                      }
                    >
                      Edit Posting
                    </button>
                  ))}
                {!token && (
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
                    <div
                      style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}
                    >
                      {applications.some(
                        (a) =>
                          a.position_id === selectedJob.position_id &&
                          a.application_status !== "Withdrawn"
                      ) ? (
                        <button
                          className="apply-btn apply-btn-applied"
                          disabled
                        >
                          Already Applied
                        </button>
                      ) : (
                        <button
                          className="apply-btn"
                          onClick={() => setApplyTarget(selectedJob)}
                        >
                          Apply Now
                        </button>
                      )}
                      <button
                        className="apply-btn"
                        style={{ backgroundColor: "#6c757d" }}
                        onClick={() =>
                          navigate(`/jobs/edit/${selectedJob.position_id}`)
                        }
                      >
                        Edit Posting
                      </button>
                    </div>
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
