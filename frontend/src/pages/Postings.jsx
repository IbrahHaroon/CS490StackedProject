import { useState, useEffect } from "react";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./Postings.css";

function PostingFormModal({ posting, onClose, onSaved }) {
  const token = localStorage.getItem("token");
  const isEditMode = !!posting;

  const [companies, setCompanies] = useState([]);
  const [formData, setFormData] = useState({
    company_name: posting?.company_name ?? "",
    title: posting?.title ?? "",
    listing_date:
      posting?.listing_date ?? new Date().toISOString().split("T")[0],
    deadline: posting?.deadline ?? "",
    salary: posting?.salary ?? "",
    location_type: posting?.location_type ?? "",
    location: posting?.location ?? "",
    education_req: posting?.education_req ?? "",
    experience_req: posting?.experience_req ?? "",
    description: posting?.description ?? "",
  });
  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api
      .get("/company/", {
        caller: "Postings.loadCompanies",
        action: "load_companies",
      })
      .then((r) => r.json())
      .then(setCompanies)
      .catch(() => {});
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    const errs = {};
    if (!formData.company_name.trim())
      errs.company_name = "Company name is required.";
    if (!formData.title.trim()) errs.title = "Job title is required.";
    if (!formData.listing_date) errs.listing_date = "Listing date is required.";
    return errs;
  };

  const resolveCompanyId = async () => {
    const match = companies.find(
      (c) => c.name.toLowerCase() === formData.company_name.trim().toLowerCase()
    );
    if (match) return match.company_id;

    const res = await api.post(
      "/company/",
      {
        name: formData.company_name.trim(),
        address: { address: "TBD", state: "N/A", zip_code: 0 },
      },
      { caller: "Postings.createCompany", action: "create_company" }
    );
    if (!res.ok) return null;
    const created = await res.json();
    return created.company_id;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    setMessage("");
    if (Object.keys(errs).length > 0) return;

    setIsSaving(true);
    logAction("form_submit", {
      component: "Postings",
      action: isEditMode ? "edit_posting" : "create_posting",
    });
    try {
      const company_id = await resolveCompanyId();
      if (!company_id) {
        setMessage("Failed to resolve company.");
        return;
      }

      const positionBody = {
        company_id,
        title: formData.title,
        listing_date: formData.listing_date,
        deadline: formData.deadline || null,
        salary: formData.salary ? Number(formData.salary) : null,
        location_type: formData.location_type || null,
        location: formData.location || null,
        education_req: formData.education_req || null,
        experience_req: formData.experience_req || null,
        description: formData.description || null,
      };

      const res = isEditMode
        ? await api.put(
            `/jobs/positions/${posting.position_id}`,
            positionBody,
            {
              caller: "Postings.updatePosting",
              action: "update_posting",
            }
          )
        : await api.post("/jobs/positions/", positionBody, {
            caller: "Postings.createPosting",
            action: "create_posting",
          });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setMessage(
          err.detail ||
            (isEditMode
              ? "Failed to update posting."
              : "Failed to create posting.")
        );
        return;
      }

      const saved = await res.json();
      onSaved(saved, isEditMode);
    } catch {
      setMessage("Network error. Please check that the server is running.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="postings-modal-overlay" onClick={onClose}>
      <div className="postings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="postings-modal-header">
          <h2 className="postings-modal-title">
            {isEditMode ? "Edit Posting" : "Add a Posting"}
          </h2>
          <button className="postings-modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="postings-modal-form">
          <label className="postings-form-label">Company Name</label>
          <input
            type="text"
            name="company_name"
            value={formData.company_name}
            onChange={handleChange}
            className="postings-form-input"
            placeholder="e.g. Acme Corp"
          />
          {errors.company_name && (
            <p className="postings-form-error">{errors.company_name}</p>
          )}

          <label className="postings-form-label">Job Title</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            className="postings-form-input"
            placeholder="e.g. Software Engineer"
          />
          {errors.title && (
            <p className="postings-form-error">{errors.title}</p>
          )}

          <label className="postings-form-label">Listing Date</label>
          <input
            type="date"
            name="listing_date"
            value={formData.listing_date}
            onChange={handleChange}
            className="postings-form-input"
          />
          {errors.listing_date && (
            <p className="postings-form-error">{errors.listing_date}</p>
          )}

          <label className="postings-form-label">
            Application Deadline (optional)
          </label>
          <input
            type="date"
            name="deadline"
            value={formData.deadline}
            onChange={handleChange}
            className="postings-form-input"
          />

          <label className="postings-form-label">Salary (optional)</label>
          <input
            type="number"
            name="salary"
            value={formData.salary}
            onChange={handleChange}
            className="postings-form-input"
            placeholder="e.g. 80000"
          />

          <label className="postings-form-label">
            Location Type (optional)
          </label>
          <select
            name="location_type"
            value={formData.location_type}
            onChange={handleChange}
            className="postings-form-input"
          >
            <option value="">Select...</option>
            <option value="Remote">Remote</option>
            <option value="Hybrid">Hybrid</option>
            <option value="Onsite">Onsite</option>
          </select>

          <label className="postings-form-label">Location (optional)</label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            className="postings-form-input"
            placeholder="e.g. New York, NY"
          />

          <label className="postings-form-label">
            Education Requirement (optional)
          </label>
          <input
            type="text"
            name="education_req"
            value={formData.education_req}
            onChange={handleChange}
            className="postings-form-input"
            placeholder="e.g. Bachelor's in CS or related field"
          />

          <label className="postings-form-label">
            Experience Requirement (optional)
          </label>
          <input
            type="text"
            name="experience_req"
            value={formData.experience_req}
            onChange={handleChange}
            className="postings-form-input"
            placeholder="e.g. 2+ years"
          />

          <label className="postings-form-label">Description (optional)</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            className="postings-form-textarea"
            placeholder="Describe the role…"
          />

          {message && <p className="postings-form-error">{message}</p>}

          <button
            type="submit"
            className="postings-form-submit"
            disabled={isSaving}
          >
            {isSaving
              ? "Saving…"
              : isEditMode
                ? "Save Changes"
                : "Create Posting"}
          </button>
        </form>
      </div>
    </div>
  );
}

function Postings() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modalPosting, setModalPosting] = useState(undefined);
  const token = localStorage.getItem("token");

  const fetchJobs = async () => {
    try {
      const res = await api.get("/jobs/positions/", {
        caller: "Postings.fetchJobs",
        action: "load_postings",
      });
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
        if (data.length > 0 && !selectedJob) setSelectedJob(data[0]);
      }
    } catch {
      // Network error handled by apiClient logging
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleSaved = (saved, isEdit) => {
    if (isEdit) {
      setJobs((prev) =>
        prev.map((j) =>
          j.position_id === saved.position_id ? { ...j, ...saved } : j
        )
      );
      setSelectedJob((prev) =>
        prev?.position_id === saved.position_id ? { ...prev, ...saved } : prev
      );
    } else {
      setJobs((prev) => [saved, ...prev]);
      setSelectedJob(saved);
      // Notify Dashboard (same tab) so it refreshes its job board immediately
      window.dispatchEvent(new CustomEvent("positionsUpdated"));
    }
    setModalPosting(undefined);
  };

  if (loading) {
    return (
      <div className="postings-page">
        <p style={{ color: "#888", padding: "2rem" }}>Loading…</p>
      </div>
    );
  }

  return (
    <div className="postings-page">
      {modalPosting !== undefined && (
        <PostingFormModal
          posting={modalPosting}
          onClose={() => setModalPosting(undefined)}
          onSaved={handleSaved}
        />
      )}

      <div className="postings-header-row">
        <h1 className="postings-title">Postings</h1>
        {token && (
          <button
            className="postings-add-btn"
            onClick={() => setModalPosting(null)}
          >
            Add a Posting
          </button>
        )}
      </div>

      <div className="postings-board">
        <div className="postings-list-wrapper">
          <h2 className="postings-list-heading">Your Postings:</h2>
          {jobs.length === 0 ? (
            <p className="postings-empty">No postings yet.</p>
          ) : (
            <div className="postings-list">
              {jobs.map((job) => (
                <div
                  key={job.position_id}
                  className={`postings-card ${
                    selectedJob?.position_id === job.position_id
                      ? "postings-card-selected"
                      : ""
                  }`}
                  onClick={() => setSelectedJob(job)}
                >
                  <span className="postings-card-company">
                    {job.company_name}
                  </span>
                  <h3 className="postings-card-title">{job.title}</h3>
                  {(job.location || job.location_type) && (
                    <span className="postings-card-meta">
                      {[job.location_type, job.location]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  )}
                  <span className="postings-card-meta">
                    {job.salary
                      ? `$${Number(job.salary).toLocaleString()}`
                      : "Salary not listed"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedJob && (
          <div className="postings-detail">
            <h2 className="postings-detail-title">
              {selectedJob.title} @ {selectedJob.company_name}
            </h2>
            {(selectedJob.location || selectedJob.location_type) && (
              <p className="postings-detail-meta">
                📍{" "}
                {[selectedJob.location_type, selectedJob.location]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            )}
            <p className="postings-detail-meta">
              {selectedJob.salary
                ? `$${Number(selectedJob.salary).toLocaleString()}`
                : "Salary not listed"}
            </p>
            <p className="postings-detail-meta">
              Listed: {selectedJob.listing_date}
            </p>

            {selectedJob.description && (
              <div className="postings-detail-section">
                <h3>Description</h3>
                <p>{selectedJob.description}</p>
              </div>
            )}
            {selectedJob.education_req && (
              <div className="postings-detail-section">
                <h3>Education</h3>
                <p>{selectedJob.education_req}</p>
              </div>
            )}
            {selectedJob.experience_req && (
              <div className="postings-detail-section">
                <h3>Experience</h3>
                <p>{selectedJob.experience_req}</p>
              </div>
            )}

            {token && (
              <button
                className="postings-edit-btn"
                onClick={() => setModalPosting(selectedJob)}
              >
                Edit Posting
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Postings;
