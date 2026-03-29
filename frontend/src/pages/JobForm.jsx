import { useState } from "react";

function JobForm() {
  // This stores all form values in one place
  const [formData, setFormData] = useState({
    jobTitle: "",
    company: "",
    status: "Applied",
    notes: "",
  });

  // Store validation errors
  const [errors, setErrors] = useState({});

  // Track loading state
  const [isSaving, setIsSaving] = useState(false);

  // Success message
  const [message, setMessage] = useState("");

  // Handle input updates
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Basic validation
  const validate = () => {
    const newErrors = {};

    if (!formData.jobTitle.trim())
      newErrors.jobTitle = "Job title is required.";

    if (!formData.company.trim())
      newErrors.company = "Company is required.";

    return newErrors;
  };

  // Handle submit
  const handleSubmit = async (e) => {
    e.preventDefault();

    const validationErrors = validate();
    setErrors(validationErrors);
    setMessage("");

    if (Object.keys(validationErrors).length > 0) return;

    setIsSaving(true);

    try {
      // Simulate backend call
      await new Promise((res) => setTimeout(res, 1000));

      setMessage("Job saved successfully.");

      // Reset form after save
      setFormData({
        jobTitle: "",
        company: "",
        status: "Applied",
        notes: "",
      });
    } catch {
      setMessage("Failed to save job.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Add Job</h1>

      <form onSubmit={handleSubmit} style={styles.card}>
        {/* Job Title */}
        <label style={styles.label}>Job Title</label>
        <input
          type="text"
          name="jobTitle"
          value={formData.jobTitle}
          onChange={handleChange}
          style={styles.input}
        />
        {errors.jobTitle && <p style={styles.error}>{errors.jobTitle}</p>}

        {/* Company */}
        <label style={styles.label}>Company</label>
        <input
          type="text"
          name="company"
          value={formData.company}
          onChange={handleChange}
          style={styles.input}
        />
        {errors.company && <p style={styles.error}>{errors.company}</p>}

        {/* Status */}
        <label style={styles.label}>Status</label>
        <select
          name="status"
          value={formData.status}
          onChange={handleChange}
          style={styles.input}
        >
          <option>Applied</option>
          <option>Interview</option>
          <option>Offer</option>
          <option>Rejected</option>
        </select>

        {/* Notes */}
        <label style={styles.label}>Notes</label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          style={styles.textarea}
        />

        {/* Button */}
        <button type="submit" style={styles.button} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Job"}
        </button>

        {/* Message */}
        {message && <p style={styles.message}>{message}</p>}
      </form>
    </div>
  );
}

// Simple styles (same approach as before)
const styles = {
  page: {
    maxWidth: "600px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: {
    fontSize: "28px",
    marginBottom: "20px",
  },
  card: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    padding: "20px",
    border: "1px solid #ddd",
    borderRadius: "12px",
  },
  label: {
    fontWeight: "600",
  },
  input: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ccc",
  },
  textarea: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    minHeight: "80px",
  },
  button: {
    marginTop: "10px",
    padding: "10px",
    borderRadius: "8px",
    border: "none",
    cursor: "pointer",
  },
  error: {
    color: "red",
    fontSize: "14px",
  },
  message: {
    color: "green",
    marginTop: "10px",
  },
};

export default JobForm;