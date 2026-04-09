import { useEffect, useState } from "react";

const API = "http://localhost:8000";

function EditModal({ title, fields, onSave, onCancel }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(fields.map((f) => [f.name, f.value]))
  );
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setError("");
    try {
      const err = await onSave(values);
      if (err) setError(err);
    } catch (e) {
      setError(e.message || "An unexpected error occurred.");
    }
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <h3 style={styles.modalTitle}>{title}</h3>
        {fields.map((f) => (
          <div key={f.name} style={styles.modalField}>
            <label style={styles.modalLabel}>{f.label}</label>
            {f.type === "textarea" ? (
              <textarea
                name={f.name}
                value={values[f.name]}
                onChange={handleChange}
                style={{ ...styles.modalInput, height: "100px", resize: "vertical" }}
                placeholder={f.placeholder || ""}
              />
            ) : (
              <input
                type={f.type || "text"}
                name={f.name}
                value={values[f.name]}
                onChange={handleChange}
                style={styles.modalInput}
                placeholder={f.placeholder || ""}
              />
            )}
          </div>
        ))}
        {error && <p style={styles.error}>{error}</p>}
        <div style={styles.modalActions}>
          <button style={styles.cancelBtn} onClick={onCancel}>
            Cancel
          </button>
          <button style={styles.saveBtn} onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

function Profile() {
  const [email, setEmail] = useState("");
  const [userId, setUserId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    Promise.all([
      fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } }).then(
        (r) => r.json()
      ),
      fetch(`${API}/profile/me`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API}/documents/me`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : [])),
    ]).then(([me, prof, docs]) => {
      setEmail(me.email || "");
      setUserId(me.user_id);
      setProfile(prof);
      setDocuments(docs);
      setLoading(false);
    });
  }, []);

  const saveProfile = async (values) => {
    let res;
    if (!profile) {
      res = await fetch(`${API}/profile/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          first_name: values.first_name || "",
          last_name: values.last_name || "",
          dob: values.dob || "2000-01-01",
          address: { address: "", state: "", zip_code: 0 },
          phone_number: values.phone_number || null,
          summary: values.summary || null,
        }),
      });
    } else {
      res = await fetch(`${API}/profile/${profile.profile_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(values),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to save.";
    }

    const updated = await res.json();
    setProfile(updated);
    setModal(null);
    setStatusMessage("Profile saved.");
    setTimeout(() => setStatusMessage(""), 3000);
    return null;
  };

  const hasResume = documents.some((d) => d.document_type.toLowerCase() === "resume");

  const completionFields = [
    { label: "First Name", done: !!profile?.first_name },
    { label: "Last Name", done: !!profile?.last_name },
    { label: "Email", done: !!email },
    { label: "Phone Number", done: !!profile?.phone_number },
    { label: "Date of Birth", done: !!profile?.dob },
    { label: "Summary", done: !!profile?.summary },
    { label: "Resume", done: hasResume },
  ];

  const completedCount = completionFields.filter((f) => f.done).length;
  const completionPct = Math.round((completedCount / completionFields.length) * 100);
  const missingFields = completionFields.filter((f) => !f.done);

  if (loading)
    return (
      <div style={styles.page}>
        <p style={{ color: "#888" }}>Loading…</p>
      </div>
    );

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Profile</h1>
      <p style={styles.subtitle}>Your account information at a glance.</p>

      {statusMessage && <p style={styles.status}>{statusMessage}</p>}

      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Profile Completion</h2>
        <p style={styles.percentageText}>{completionPct}% complete</p>
        <div style={styles.progressBar}>
          <div style={{ ...styles.progressFill, width: `${completionPct}%` }} />
        </div>
        <p style={styles.helperText}>
          {completedCount} of {completionFields.length} items complete
        </p>
      </div>

      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>Profile Summary</h2>
          <button style={styles.editBtn} onClick={() => setModal("info")}>
            Edit
          </button>
        </div>
        <div style={styles.summaryGrid}>
          <InfoRow label="First Name" value={profile?.first_name} />
          <InfoRow label="Last Name" value={profile?.last_name} />
          <InfoRow label="Email" value={email} />
          <InfoRow label="Phone" value={profile?.phone_number} />
          <InfoRow label="Date of Birth" value={profile?.dob} />
          <InfoRow label="Resume" value={hasResume ? "Uploaded" : "Not uploaded"} />
        </div>
      </div>

      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>About</h2>
          <button style={styles.editBtn} onClick={() => setModal("about")}>
            Edit
          </button>
        </div>
        {profile?.summary ? (
          <p style={styles.summaryText}>{profile.summary}</p>
        ) : (
          <p style={{ color: "#aaa", fontSize: "14px" }}>No summary added yet.</p>
        )}
      </div>

      {missingFields.length > 0 && (
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Missing Information</h2>
          <ul style={styles.missingList}>
            {missingFields.map((f) => (
              <li key={f.label} style={styles.missingItem}>
                {f.label} —{" "}
                <span style={{ color: "#888" }}>
                  {f.label === "Resume"
                    ? "upload via Document Library"
                    : "update above"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {modal === "info" && (
        <EditModal
          title="Edit Profile Info"
          fields={[
            {
              name: "first_name",
              label: "First Name",
              value: profile?.first_name || "",
            },
            { name: "last_name", label: "Last Name", value: profile?.last_name || "" },
            {
              name: "phone_number",
              label: "Phone Number",
              value: profile?.phone_number || "",
              placeholder: "555-0100",
            },
            {
              name: "dob",
              label: "Date of Birth",
              value: profile?.dob || "",
              type: "date",
            },
          ]}
          onSave={saveProfile}
          onCancel={() => setModal(null)}
        />
      )}

      {modal === "about" && (
        <EditModal
          title="Edit About"
          fields={[
            {
              name: "summary",
              label: "Summary",
              value: profile?.summary || "",
              type: "textarea",
              placeholder: "Tell us about yourself…",
            },
          ]}
          onSave={saveProfile}
          onCancel={() => setModal(null)}
        />
      )}
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div>
      <p style={styles.summaryLabel}>{label}</p>
      <p style={styles.summaryValue}>
        {value || <span style={{ color: "#aaa" }}>Not set</span>}
      </p>
    </div>
  );
}

const styles = {
  page: {
    maxWidth: "900px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: { fontSize: "32px", marginBottom: "8px" },
  subtitle: { color: "#555", marginBottom: "24px" },
  status: { color: "green", fontSize: "14px", marginBottom: "12px" },
  card: {
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    borderRadius: "12px",
    padding: "24px",
    marginBottom: "20px",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },
  cardTitle: { fontSize: "22px", margin: 0, color: "#444" },
  editBtn: {
    padding: "4px 14px",
    border: "1px solid #ccc",
    borderRadius: "6px",
    background: "none",
    cursor: "pointer",
    fontSize: "14px",
    color: "#333",
  },
  percentageText: { fontSize: "24px", fontWeight: "700", color: "#333" },
  progressBar: {
    width: "100%",
    height: "14px",
    backgroundColor: "#e5e7eb",
    borderRadius: "999px",
    overflow: "hidden",
    margin: "10px 0",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#22c55e",
    transition: "width 0.3s ease",
  },
  helperText: { fontSize: "14px", color: "#555" },
  summaryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
  },
  summaryLabel: { fontSize: "13px", color: "#555", margin: 0 },
  summaryValue: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#222",
    wordBreak: "break-word",
    margin: "4px 0 0",
  },
  summaryText: { fontSize: "15px", color: "#333", lineHeight: "1.6" },
  missingList: { paddingLeft: "20px" },
  missingItem: { marginBottom: "8px", color: "#333" },
  // Modal
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.4)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modal: {
    background: "#fff",
    borderRadius: "12px",
    padding: "28px",
    width: "100%",
    maxWidth: "400px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  modalTitle: { margin: 0, fontSize: "18px", color: "#222" },
  modalField: { display: "flex", flexDirection: "column", gap: "4px" },
  modalLabel: { fontSize: "14px", fontWeight: "600", color: "#333" },
  modalInput: {
    padding: "8px 10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
  },
  modalActions: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "10px",
    marginTop: "8px",
  },
  cancelBtn: {
    padding: "8px 16px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    background: "none",
    cursor: "pointer",
    color: "#333",
  },
  saveBtn: {
    padding: "8px 16px",
    borderRadius: "6px",
    border: "none",
    background: "#4f8ef7",
    color: "#fff",
    cursor: "pointer",
  },
  error: { color: "red", fontSize: "13px", margin: 0 },
};

export default Profile;
