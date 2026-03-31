import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const API = "http://localhost:8000";

function JobForm() {
  const { id } = useParams();
  const isEditMode = !!id;

  const [companies, setCompanies] = useState([]);
  const [formData, setFormData] = useState({
    company_name: "",
    title: "",
    listing_date: new Date().toISOString().split("T")[0],
    salary: "",
    education_req: "",
    experience_req: "",
    description: "",
  });
  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [loading, setLoading] = useState(isEditMode);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetch(`${API}/company/`)
      .then((r) => r.json())
      .then((data) => {
        setCompanies(data);
        return data;
      })
      .then(async (data) => {
        if (!isEditMode) return;
        try {
          const res = await fetch(`${API}/jobs/positions/${id}`);
          if (!res.ok) {
            setMessage("Failed to load job posting.");
            return;
          }
          const pos = await res.json();
          const company = data.find((c) => c.company_id === pos.company_id);
          setFormData({
            company_name: company ? company.name : String(pos.company_id),
            title: pos.title,
            listing_date: pos.listing_date,
            salary: pos.salary ?? "",
            education_req: pos.education_req ?? "",
            experience_req: pos.experience_req ?? "",
            description: pos.description ?? "",
          });
        } finally {
          setLoading(false);
        }
      });
  }, [id, isEditMode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    const errs = {};
    if (!formData.company_name.trim()) errs.company_name = "Company name is required.";
    if (!formData.title.trim()) errs.title = "Job title is required.";
    if (!formData.listing_date) errs.listing_date = "Listing date is required.";
    return errs;
  };

  const resolveCompanyId = async () => {
    const match = companies.find(
      (c) => c.name.toLowerCase() === formData.company_name.trim().toLowerCase()
    );
    if (match) return match.company_id;

    // Company doesn't exist — create it with a placeholder address
    const res = await fetch(`${API}/company/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        name: formData.company_name.trim(),
        address: { address: "TBD", state: "N/A", zip_code: 0 },
      }),
    });
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

    try {
      const company_id = await resolveCompanyId();
      if (!company_id) {
        setMessage("Failed to resolve company.");
        return;
      }

      const url = isEditMode ? `${API}/jobs/positions/${id}` : `${API}/jobs/positions/`;
      const method = isEditMode ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_id,
          title: formData.title,
          listing_date: formData.listing_date,
          salary: formData.salary ? Number(formData.salary) : null,
          education_req: formData.education_req || null,
          experience_req: formData.experience_req || null,
          description: formData.description || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setMessage(
          err.detail ||
            (isEditMode ? "Failed to update posting." : "Failed to create posting.")
        );
        return;
      }

      setMessage(
        isEditMode ? "Posting updated successfully." : "Posting created successfully."
      );
      setTimeout(() => navigate("/"), 1500);
    } catch (err) {
      setMessage("Network error. Please check that the server is running.");
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.page}>
        <p style={{ color: "#888" }}>Loading…</p>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>{isEditMode ? "Edit Posting" : "Add Posting"}</h1>
      <form onSubmit={handleSubmit} style={styles.card}>
        <label style={styles.label}>Company Name</label>
        <input
          type="text"
          name="company_name"
          value={formData.company_name}
          onChange={handleChange}
          style={styles.input}
          placeholder="e.g. Acme Corp"
        />
        {errors.company_name && <p style={styles.error}>{errors.company_name}</p>}

        <label style={styles.label}>Job Title</label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          style={styles.input}
          placeholder="e.g. Software Engineer"
        />
        {errors.title && <p style={styles.error}>{errors.title}</p>}

        <label style={styles.label}>Listing Date</label>
        <input
          type="date"
          name="listing_date"
          value={formData.listing_date}
          onChange={handleChange}
          style={styles.input}
        />
        {errors.listing_date && <p style={styles.error}>{errors.listing_date}</p>}

        <label style={styles.label}>Salary (optional)</label>
        <input
          type="number"
          name="salary"
          value={formData.salary}
          onChange={handleChange}
          style={styles.input}
          placeholder="e.g. 80000"
        />

        <label style={styles.label}>Education Requirement (optional)</label>
        <input
          type="text"
          name="education_req"
          value={formData.education_req}
          onChange={handleChange}
          style={styles.input}
          placeholder="e.g. Bachelor's in CS"
        />

        <label style={styles.label}>Experience Requirement (optional)</label>
        <input
          type="text"
          name="experience_req"
          value={formData.experience_req}
          onChange={handleChange}
          style={styles.input}
          placeholder="e.g. 2+ years React"
        />

        <label style={styles.label}>Description (optional)</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          style={styles.textarea}
          placeholder="Describe the role…"
        />

        <button type="submit" style={styles.button} disabled={isSaving}>
          {isSaving ? "Saving…" : isEditMode ? "Save Changes" : "Create Posting"}
        </button>

        {message && (
          <p
            style={{
              ...styles.message,
              color: message.includes("Failed") ? "red" : "green",
            }}
          >
            {message}
          </p>
        )}
      </form>
    </div>
  );
}

const styles = {
  page: {
    maxWidth: "600px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: { fontSize: "28px", marginBottom: "20px" },
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    padding: "20px",
    border: "1px solid #ddd",
    borderRadius: "12px",
  },
  label: { fontWeight: "600" },
  input: { padding: "10px", borderRadius: "8px", border: "1px solid #ccc" },
  textarea: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    minHeight: "100px",
  },
  button: {
    marginTop: "10px",
    padding: "10px",
    borderRadius: "8px",
    border: "none",
    cursor: "pointer",
    backgroundColor: "#4f8ef7",
    color: "#fff",
    fontSize: "1rem",
  },
  error: { color: "red", fontSize: "14px", margin: 0 },
  message: { marginTop: "10px" },
};

export default JobForm;
