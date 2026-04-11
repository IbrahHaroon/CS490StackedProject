import { useState, useEffect } from "react";
import "./CareerPreferences.css";

const API = "http://localhost:8000";

const WORK_MODES = ["Any", "Remote", "Hybrid", "On-site"];

function CareerPreferences() {
  const [form, setForm] = useState({
    target_roles: "",
    location_preferences: "",
    work_mode: "Any",
    salary_preference: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API}/career-preferences/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (data) {
            setForm({
              target_roles: data.target_roles || "",
              location_preferences: data.location_preferences || "",
              work_mode: data.work_mode || "Any",
              salary_preference: data.salary_preference || "",
            });
          }
        }
      } catch (err) {
        console.error("Failed to load preferences:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSuccess("");
    setError("");
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess("");
    setError("");
    try {
      const res = await fetch(`${API}/career-preferences/me`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          target_roles: form.target_roles || null,
          location_preferences: form.location_preferences || null,
          work_mode: form.work_mode === "Any" ? null : form.work_mode,
          salary_preference: form.salary_preference || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setError(err.detail || "Failed to save preferences.");
      } else {
        setSuccess("Preferences saved successfully.");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="career-prefs-page">
        <p className="career-prefs-placeholder">Loading…</p>
      </div>
    );

  return (
    <div className="career-prefs-page">
      <h1 className="career-prefs-title">Career Preferences</h1>
      <p className="career-prefs-subtitle">
        Tell us what you're looking for so we can surface the best matches.
      </p>

      <form className="career-prefs-form" onSubmit={handleSave}>
        <div className="career-prefs-field">
          <label htmlFor="target_roles">Target Roles</label>
          <input
            id="target_roles"
            type="text"
            placeholder="e.g. Software Engineer, Frontend Developer, Data Analyst"
            value={form.target_roles}
            onChange={(e) => handleChange("target_roles", e.target.value)}
          />
          <span className="career-prefs-hint">
            Comma-separated list of roles you're interested in.
          </span>
        </div>

        <div className="career-prefs-field">
          <label htmlFor="location_preferences">Location Preferences</label>
          <input
            id="location_preferences"
            type="text"
            placeholder="e.g. New York, NY; San Francisco, CA; Austin, TX"
            value={form.location_preferences}
            onChange={(e) =>
              handleChange("location_preferences", e.target.value)
            }
          />
          <span className="career-prefs-hint">
            Cities or regions you'd like to work in.
          </span>
        </div>

        <div className="career-prefs-field">
          <label>Work Mode</label>
          <div className="career-prefs-radio-group">
            {WORK_MODES.map((mode) => (
              <label key={mode} className="career-prefs-radio-label">
                <input
                  type="radio"
                  name="work_mode"
                  value={mode}
                  checked={form.work_mode === mode}
                  onChange={() => handleChange("work_mode", mode)}
                />
                {mode}
              </label>
            ))}
          </div>
        </div>

        <div className="career-prefs-field">
          <label htmlFor="salary_preference">Salary Expectation</label>
          <input
            id="salary_preference"
            type="text"
            placeholder="e.g. $80,000 – $120,000 / year"
            value={form.salary_preference}
            onChange={(e) => handleChange("salary_preference", e.target.value)}
          />
          <span className="career-prefs-hint">
            Your expected salary range.
          </span>
        </div>

        {error && <p className="career-prefs-error">{error}</p>}
        {success && <p className="career-prefs-success">{success}</p>}

        <button
          type="submit"
          className="career-prefs-save-btn"
          disabled={saving}
        >
          {saving ? "Saving…" : "Save Preferences"}
        </button>
      </form>

      {/* Summary card */}
      {(form.target_roles ||
        form.location_preferences ||
        form.salary_preference) && (
        <div className="career-prefs-summary">
          <h2 className="career-prefs-summary-title">Your Current Preferences</h2>
          <div className="career-prefs-summary-grid">
            {form.target_roles && (
              <div className="career-prefs-summary-item">
                <span className="career-prefs-summary-label">Target Roles</span>
                <span className="career-prefs-summary-value">
                  {form.target_roles}
                </span>
              </div>
            )}
            {form.location_preferences && (
              <div className="career-prefs-summary-item">
                <span className="career-prefs-summary-label">Locations</span>
                <span className="career-prefs-summary-value">
                  {form.location_preferences}
                </span>
              </div>
            )}
            <div className="career-prefs-summary-item">
              <span className="career-prefs-summary-label">Work Mode</span>
              <span className="career-prefs-summary-value">
                {form.work_mode}
              </span>
            </div>
            {form.salary_preference && (
              <div className="career-prefs-summary-item">
                <span className="career-prefs-summary-label">Salary</span>
                <span className="career-prefs-summary-value">
                  {form.salary_preference}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default CareerPreferences;
