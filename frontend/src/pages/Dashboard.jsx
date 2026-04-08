import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Dashboard.css";

const API = "http://localhost:8000";

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

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [applyTarget, setApplyTarget] = useState(null);
  const [applySuccess, setApplySuccess] = useState("");
  const jobBoardRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchAll = async () => {
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

      setLoading(false);
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
    // Refresh applications preview
    const appRes = await fetch(`${API}/jobs/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (appRes.ok) setApplications(await appRes.json());
    return null;
  };

  const scrollToJobBoard = () => {
    jobBoardRef.current?.scrollIntoView({ behavior: "smooth" });
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
          onClose={() => setApplyTarget(null)}
          onConfirm={handleApply}
        />
      )}
      <h1 className="dashboard-welcome">Welcome</h1>
      {applySuccess && <p className="apply-success-msg">{applySuccess}</p>}

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
                  <span className="preview-job-company">{job.company_name}</span>
                  <span className="preview-job-title">{job.title}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="preview-card preview-card-apps">
          <div className="preview-card-header">
            <h2>Current Apps</h2>
            <button className="view-more-btn" onClick={() => navigate("/applications")}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {applications.length === 0 ? (
              <p className="preview-placeholder">No applications yet.</p>
            ) : (
              applications.slice(0, 2).map((app) => (
                <div key={app.job_id} className="preview-job-item">
                  <span className="preview-job-company">{app.application_status}</span>
                  <span className="preview-job-title">Application #{app.job_id}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="preview-card preview-card-docs">
          <div className="preview-card-header">
            <h2>Documents</h2>
            <button className="view-more-btn" onClick={() => navigate("/documents")}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {documents.length === 0 ? (
              <p className="preview-placeholder">No documents yet.</p>
            ) : (
              documents.slice(0, 2).map((doc) => (
                <div key={doc.doc_id} className="preview-job-item">
                  <span className="preview-job-company">{doc.document_type}</span>
                  <span className="preview-job-title">
                    {doc.document_location.split("/").pop()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Full job board */}
      <div className="job-board" ref={jobBoardRef}>
        {jobs.length === 0 ? (
          <p style={{ color: "#888", padding: "1rem" }}>No job listings available.</p>
        ) : (
          <>
            <div className="job-board-list">
              {jobs.map((job) => (
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
                <h2 className="job-detail-title">
                  {selectedJob.title} @ {selectedJob.company_name}
                </h2>
                <p className="job-detail-meta">
                  {selectedJob.salary
                    ? `$${Number(selectedJob.salary).toLocaleString()}`
                    : "Salary not listed"}
                </p>
                <p className="job-detail-meta">Listed: {selectedJob.listing_date}</p>

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
                      onClick={() => setApplyTarget(selectedJob)}
                    >
                      Apply Now
                    </button>
                  ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
