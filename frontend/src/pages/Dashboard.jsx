import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./Dashboard.css";

// Extract city portion from a location string so variants like
// "New York, NY" and "New York" resolve to the same filter bucket.
const normalizeLocation = (loc) => {
  if (!loc) return "";
  return loc.split(",")[0].trim();
};

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

function DocViewerModal({ doc, onClose, token }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!doc || !token) return;
    setLoading(true);
    api
      .get(`/documents/${doc.doc_id}/content`, {
        caller: "Dashboard.DocViewerModal",
        action: "fetch_document_content",
      })
      .then((r) => r.json())
      .then((data) => setContent(data.content || ""))
      .catch(() => setContent(""))
      .finally(() => setLoading(false));
  }, [doc, token]);

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
            <h3 className="apply-modal-title">
              {doc.document_name || "Resume"}
            </h3>
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

function CompanyResearchSection({
  job,
  token,
  applications,
  onApplicationsChange,
}) {
  const existingApp = applications?.find(
    (a) => a.position_id === job?.position_id
  );
  const existingNotes = existingApp?.company_research_notes || "";

  const [prompt, setPrompt] = useState("");
  const [notes, setNotes] = useState(existingNotes);
  const [researchLoading, setResearchLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [savedJobId, setSavedJobId] = useState(existingApp?.job_id ?? null);
  const [saveStatus, setSaveStatus] = useState(""); // "saved" | "error" | ""
  const [researchError, setResearchError] = useState("");

  // When the selected job changes, reset to that job's saved notes
  useEffect(() => {
    const app = applications?.find((a) => a.position_id === job?.position_id);
    setNotes(app?.company_research_notes || "");
    setSavedJobId(app?.job_id ?? null);
    setPrompt("");
    setResearchError("");
    setSaveStatus("");
  }, [job?.position_id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleResearch = async () => {
    if (researchLoading) return;
    setResearchLoading(true);
    setResearchError("");
    try {
      const res = await api.post(
        "/documents/company-research",
        { position_id: job.position_id, context: prompt },
        {
          caller: "Dashboard.CompanyResearchSection",
          action: "company_research",
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Company research failed.");
      }
      const data = await res.json();
      setNotes(data.research);
      setSavedJobId(data.job_id);
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(""), 3000);
      // Sync applications state so the notes survive a job re-select
      if (onApplicationsChange) {
        onApplicationsChange((prev) => {
          const exists = prev.some((a) => a.job_id === data.job_id);
          if (exists) {
            return prev.map((a) =>
              a.job_id === data.job_id
                ? { ...a, company_research_notes: data.research }
                : a
            );
          }
          return [
            ...prev,
            {
              job_id: data.job_id,
              position_id: job.position_id,
              company_research_notes: data.research,
              application_status: "Interested",
            },
          ];
        });
      }
    } catch (err) {
      setResearchError(err.message || "An error occurred.");
    } finally {
      setResearchLoading(false);
    }
  };

  const handleSave = async () => {
    if (!savedJobId || saveLoading) return;
    setSaveLoading(true);
    setSaveStatus("");
    try {
      const res = await api.put(
        `/jobs/applications/${savedJobId}`,
        { company_research_notes: notes },
        {
          caller: "Dashboard.CompanyResearchSection",
          action: "save_research_notes",
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to save notes.");
      }
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(""), 3000);
      if (onApplicationsChange) {
        onApplicationsChange((prev) =>
          prev.map((a) =>
            a.job_id === savedJobId
              ? { ...a, company_research_notes: notes }
              : a
          )
        );
      }
    } catch (err) {
      setSaveStatus("error");
    } finally {
      setSaveLoading(false);
    }
  };

  if (!token) return null;

  return (
    <div className="company-research-section">
      <h3 className="company-research-title">Research {job.company_name}</h3>

      {/* Prompt input */}
      <p className="company-research-hint">
        Add context or questions for targeted AI insights.
      </p>
      <textarea
        className="company-research-textarea"
        placeholder={`e.g. What's the culture like at ${job.company_name}? How should I prepare for an interview here?`}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={2}
        disabled={researchLoading}
      />
      <button
        className="company-research-btn"
        onClick={handleResearch}
        disabled={researchLoading}
      >
        {researchLoading ? "Researching…" : "Research Company"}
      </button>
      {researchError && (
        <p className="company-research-error">{researchError}</p>
      )}

      {/* Editable notes — always shown, pre-populated with saved or generated content */}
      {(notes || savedJobId) && (
        <div className="company-research-notes-area">
          <div className="company-research-notes-header">
            <span className="company-research-notes-label">Notes</span>
            {saveStatus === "saved" && (
              <span className="company-research-save-status company-research-save-status--ok">
                Saved
              </span>
            )}
            {saveStatus === "error" && (
              <span className="company-research-save-status company-research-save-status--err">
                Save failed
              </span>
            )}
          </div>
          <textarea
            className="company-research-textarea company-research-textarea--notes"
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              setSaveStatus("");
            }}
            rows={6}
            disabled={saveLoading}
          />
          <button
            className="company-research-save-btn"
            onClick={handleSave}
            disabled={saveLoading || !savedJobId}
          >
            {saveLoading ? "Saving…" : "Save Notes"}
          </button>
        </div>
      )}
    </div>
  );
}

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
  const [jobs, setJobs] = useState([]); // recruiter-posted only (job board)
  const [positionMap, setPositionMap] = useState({}); // all positions keyed by id (for lookup)
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
  const [firstName, setFirstName] = useState("");
  const [sortOrder, setSortOrder] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterLocationType, setFilterLocationType] = useState("");
  const [filterLocation, setFilterLocation] = useState("");
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

  const fetchJobsOnly = async () => {
    try {
      const posRes = await api.get("/jobs/positions/?include_manual=true", {
        caller: "Dashboard.fetchJobsOnly",
        action: "refresh_positions",
      });
      if (posRes.ok) {
        const data = await posRes.json();
        const boardJobs = data.filter((p) => !p.is_manual);
        setJobs(boardJobs);
        const map = {};
        for (const p of data) map[p.position_id] = p;
        setPositionMap(map);
      }
    } catch (err) {
      // handled by api client
    }
  };

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const posRes = await api.get("/jobs/positions/?include_manual=true", {
          caller: "Dashboard.fetchAll",
          action: "load_positions",
        });
        if (posRes.ok) {
          const data = await posRes.json();
          const boardJobs = data.filter((p) => !p.is_manual);
          setJobs(boardJobs);
          const map = {};
          for (const p of data) map[p.position_id] = p;
          setPositionMap(map);
        }

        // Applications, documents, and metrics require auth
        if (token) {
          const [appRes, docRes, metricsRes, meRes] = await Promise.all([
            api.get("/jobs/dashboard", {
              caller: "Dashboard.fetchAll",
              action: "load_applications",
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
          if (appRes.ok) setApplications(await appRes.json());
          if (docRes.ok) setDocuments(await docRes.json());
          if (metricsRes.ok) setMetrics(await metricsRes.json());
          if (meRes.ok) {
            const profile = await meRes.json();
            setFirstName(profile.first_name || "");
          }
        }
      } catch (err) {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [location.pathname, token]);

  // Re-fetch jobs when a new posting is added from the Postings page
  useEffect(() => {
    const handlePositionsUpdated = () => fetchJobsOnly();
    const handleFocus = () => fetchJobsOnly();
    window.addEventListener("positionsUpdated", handlePositionsUpdated);
    window.addEventListener("focus", handleFocus);
    return () => {
      window.removeEventListener("positionsUpdated", handlePositionsUpdated);
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  // Open a specific job card when navigated here from Documents page (?job=<position_id>)
  useEffect(() => {
    const pid = searchParams.get("job");
    if (!pid || jobs.length === 0) return;
    const target = jobs.find((j) => String(j.position_id) === pid);
    if (target) {
      setSelectedJob(target);
      setSearchParams({}, { replace: true });
      setTimeout(
        () => jobBoardRef.current?.scrollIntoView({ behavior: "smooth" }),
        100
      );
    }
  }, [searchParams, jobs]);

  const handleApply = async (position_id) => {
    const meRes = await api.get("/auth/me", {
      caller: "Dashboard.handleApply",
      action: "verify_auth",
    });
    if (!meRes.ok) return "You must be signed in to apply.";
    const me = await meRes.json();

    const res = await api.post(
      "/jobs/applications/",
      {
        user_id: me.user_id,
        position_id,
        years_of_experience: 0,
      },
      { caller: "Dashboard.handleApply", action: "submit_application" }
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Application failed.";
    }

    setApplyTarget(null);
    setApplySuccess(`Applied to ${applyTarget?.title}!`);
    setTimeout(() => setApplySuccess(""), 3000);
    const appRes = await api.get("/jobs/dashboard", {
      caller: "Dashboard.handleApply",
      action: "refresh_applications",
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
          ? "/documents/generate-resume"
          : "/documents/generate-cover-letter";

      const res = await api.post(
        endpoint,
        { position_id },
        {
          caller: "Dashboard.handleGenerateAIDoc",
          action: `generate_ai_${docType.toLowerCase().replace(" ", "_")}`,
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to generate AI ${docType}.`);
      }

      const newDoc = await res.json();
      // Refetch documents so job-resume links are current
      const docRes = await api.get("/documents/me", {
        caller: "Dashboard.handleGenerateAIDoc",
        action: "refresh_documents",
      });
      if (docRes.ok) setDocuments(await docRes.json());
      else
        setDocuments((prev) => [
          ...prev,
          {
            doc_id: newDoc.doc_id,
            document_type: docType,
            document_name: newDoc.document_name,
            job_id: newDoc.job_id ?? null,
          },
        ]);

      setSelectedDoc(newDoc.doc_id);
      setApplySuccess(`AI ${docType} generated successfully!`);
      setTimeout(() => setApplySuccess(""), 3000);
    } catch (err) {
      // handled by api client
    } finally {
      setAiGenerating(false);
    }
  };

  // Build position_id → resume docs map so job cards can show linked resumes.
  // Path: doc.job_id → applied_job.job_id → applied_job.position_id
  const positionResumeMap = {};
  for (const doc of documents) {
    if (doc.document_type === "Resume" && doc.job_id) {
      const app = applications.find((a) => a.job_id === doc.job_id);
      if (app) {
        if (!positionResumeMap[app.position_id])
          positionResumeMap[app.position_id] = [];
        positionResumeMap[app.position_id].push(doc);
      }
    }
  }

  const uniqueLocations = [
    ...new Map(
      jobs
        .filter((j) => j.location)
        .map((j) => [
          normalizeLocation(j.location).toLowerCase(),
          normalizeLocation(j.location),
        ])
    ).values(),
  ].sort();
  const uniqueCompanies = [
    ...new Set(jobs.map((j) => j.company_name).filter(Boolean)),
  ].sort();
  const hasActiveFilters =
    filterLocationType ||
    filterLocation ||
    filterCompany ||
    filterTitle ||
    filterMinSalary ||
    filterMaxSalary;

  const clearFilters = () => {
    setFilterLocationType("");
    setFilterLocation("");
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
          job.location_type?.toLowerCase().includes(q)
        );
      })
    : jobs;

  if (filterLocationType) {
    filteredJobs = filteredJobs.filter(
      (j) => j.location_type?.toLowerCase() === filterLocationType.toLowerCase()
    );
  }
  if (filterLocation) {
    filteredJobs = filteredJobs.filter(
      (j) =>
        normalizeLocation(j.location).toLowerCase() ===
        filterLocation.toLowerCase()
    );
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
      (a, b) => new Date(a.listing_date) - new Date(b.listing_date)
    );
  } else if (sortOrder === "date-desc") {
    filteredJobs = [...filteredJobs].sort(
      (a, b) => new Date(b.listing_date) - new Date(a.listing_date)
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

  // Renders linked resumes for a job inside the detail panel / expanded modal
  const renderLinkedResumes = (job) => {
    const resumes = positionResumeMap[job.position_id];
    if (!resumes || resumes.length === 0) return null;
    return (
      <div className="job-detail-section">
        <h3>Generated Resume{resumes.length > 1 ? "s" : ""}</h3>
        {resumes.map((doc) => (
          <button
            key={doc.doc_id}
            className="job-linked-resume-btn"
            onClick={() => setViewingDoc(doc)}
          >
            {doc.document_name || `Resume #${doc.doc_id}`}
          </button>
        ))}
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
      {viewingDoc && (
        <DocViewerModal
          doc={viewingDoc}
          token={token}
          onClose={() => setViewingDoc(null)}
        />
      )}
      <h1 className="dashboard-welcome">
        Welcome{firstName ? `, ${firstName}` : ""}
      </h1>
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
              [...applications]
                .sort((a, b) => b.job_id - a.job_id)
                .slice(0, 3)
                .map((app) => {
                  const pos = positionMap[app.position_id];
                  return (
                    <div key={app.job_id} className="preview-job-item">
                      <div className="preview-job-item-top">
                        <span className="preview-job-company">
                          {pos?.company_name || "—"}
                        </span>
                        <span
                          className={`preview-status-badge preview-status-${app.application_status?.toLowerCase()}`}
                        >
                          {app.application_status}
                        </span>
                      </div>
                      <span className="preview-job-title">
                        {pos?.title || `Application #${app.job_id}`}
                      </span>
                    </div>
                  );
                })
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
                  <label className="filter-panel-label">Work Type</label>
                  <select
                    className="filter-panel-select"
                    value={filterLocationType}
                    onChange={(e) => setFilterLocationType(e.target.value)}
                  >
                    <option value="">All</option>
                    <option value="Remote">Remote</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="Onsite">In-Person</option>
                  </select>
                </div>
                <div className="filter-panel-row">
                  <label className="filter-panel-label">Location</label>
                  <select
                    className="filter-panel-select"
                    value={filterLocation}
                    onChange={(e) => setFilterLocation(e.target.value)}
                  >
                    <option value="">All</option>
                    {uniqueLocations.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
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
              ? "No job listings available."
              : "No jobs match your search."}
          </p>
        ) : (
          <>
            <div className="job-board-list">
              {filteredJobs.map((job) => {
                const cardResumes = positionResumeMap[job.position_id];
                return (
                  <div
                    key={job.position_id}
                    className={`job-card ${
                      selectedJob?.position_id === job.position_id
                        ? "job-card-selected"
                        : ""
                    }`}
                    onClick={() => setSelectedJob(job)}
                  >
                    <div className="job-card-top-row">
                      <span className="job-card-company">
                        {job.company_name}
                      </span>
                      {(() => {
                        const app = applications.find(
                          (a) =>
                            a.position_id === job.position_id &&
                            a.application_status !== "Withdrawn"
                        );
                        return app ? (
                          <span
                            className={`preview-status-badge preview-status-${app.application_status?.toLowerCase()}`}
                          >
                            {app.application_status}
                          </span>
                        ) : null;
                      })()}
                    </div>
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
                    <DeadlineBadge deadline={job.deadline} />
                    {cardResumes?.length > 0 && (
                      <div className="job-card-resume-row">
                        {cardResumes.slice(-1).map((doc) => (
                          <button
                            key={doc.doc_id}
                            className="job-card-resume-link"
                            onClick={(e) => {
                              e.stopPropagation();
                              setViewingDoc(doc);
                            }}
                          >
                            📄 {doc.document_name || "View Resume"}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
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
                {selectedJob.deadline && (
                  <DeadlineBadge
                    deadline={selectedJob.deadline}
                    className="job-detail-meta"
                  />
                )}

                {renderLinkedResumes(selectedJob)}

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

                <CompanyResearchSection
                  job={selectedJob}
                  token={token}
                  applications={applications}
                  onApplicationsChange={setApplications}
                />

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
                  {selectedJob.deadline && (
                    <DeadlineBadge
                      deadline={selectedJob.deadline}
                      className="job-detail-meta"
                    />
                  )}

                  {renderLinkedResumes(selectedJob)}

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

                  <CompanyResearchSection
                    job={selectedJob}
                    token={token}
                    applications={applications}
                    onApplicationsChange={setApplications}
                  />

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
