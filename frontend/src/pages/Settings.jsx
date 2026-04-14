import { useState, useEffect } from "react";
import EditModal from "../components/EditModal";

const API = "http://localhost:8000";

function Section({ title, children, onEdit }) {
  return (
    <div style={styles.section}>
      <div style={styles.sectionHeader}>
        <h2 style={styles.sectionTitle}>{title}</h2>
        <button type="button" style={styles.editBtn} onClick={onEdit}>
          Edit
        </button>
      </div>
      {children}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div style={styles.field}>
      <span style={styles.fieldLabel}>{label}</span>
      <span style={styles.fieldValue}>
        {value || <em style={{ color: "#aaa" }}>Not set</em>}
      </span>
    </div>
  );
}

function ChangePasswordModal({ onCancel }) {
  const [current, setCurrent] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const token = localStorage.getItem("token");

  const handleSave = async () => {
    setError("");
    setSuccess("");
    if (!current) return setError("Current password is required.");
    if (newPw.length < 6)
      return setError("New password must be at least 6 characters.");
    if (newPw !== confirm) return setError("Passwords do not match.");

    const res = await fetch(`${API}/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ current_password: current, new_password: newPw }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return setError(err.detail || "Failed to update password.");
    }

    setSuccess("Password updated successfully.");
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <h3 style={styles.modalTitle}>Change Password</h3>
        <div style={styles.modalField}>
          <label style={styles.modalLabel}>Current Password</label>
          <input
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            style={styles.modalInput}
            placeholder="••••••••"
          />
        </div>
        <div style={styles.modalField}>
          <label style={styles.modalLabel}>New Password</label>
          <input
            type="password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            style={styles.modalInput}
            placeholder="••••••••"
          />
        </div>
        <div style={styles.modalField}>
          <label style={styles.modalLabel}>Confirm New Password</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            style={styles.modalInput}
            placeholder="••••••••"
          />
        </div>
        {error && <p style={{ color: "red", fontSize: "13px" }}>{error}</p>}
        {success && (
          <p style={{ color: "green", fontSize: "13px" }}>{success}</p>
        )}
        <div style={styles.modalActions}>
          <button style={styles.cancelBtn} onClick={onCancel}>
            {success ? "Close" : "Cancel"}
          </button>
          {!success && (
            <button style={styles.saveBtn} onClick={handleSave}>
              Update Password
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Settings() {
  const [profile, setProfile] = useState(null);
  const [email, setEmail] = useState("");
  const [modal, setModal] = useState(null); // null | "name" | "contact" | "password"
  const [statusMessage, setStatusMessage] = useState("");
  const [emailNotifications, setEmailNotifications] = useState(
    () => localStorage.getItem("emailNotifications") !== "false"
  );
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem("darkMode") !== "false"
  );

  useEffect(() => {
    if (darkMode) {
      document.body.classList.remove("light-mode");
    } else {
      document.body.classList.add("light-mode");
    }
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  useEffect(() => {
    localStorage.setItem("emailNotifications", emailNotifications);
  }, [emailNotifications]);

  const token = localStorage.getItem("token");

  useEffect(() => {
    if (!token) return;

    fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((d) => setEmail(d.email || ""));

    fetch(`${API}/profile/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setProfile(d);
      });
  }, []);

  const saveProfile = async (values) => {
    const res = await fetch(`${API}/profile/${profile.profile_id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(values),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to save.";
    }

    const updated = await res.json();
    setProfile(updated);
    setModal(null);
    setStatusMessage("Settings saved.");
    setTimeout(() => setStatusMessage(""), 3000);
    return null;
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Settings</h1>
      <p style={styles.subtitle}>Manage your account preferences.</p>

      {statusMessage && <p style={styles.status}>{statusMessage}</p>}

      <div style={styles.formCard}>
        {/* Account */}
        <Section title="Account" onEdit={() => setModal("name")}>
          <Field label="First Name" value={profile?.first_name} />
          <Field label="Last Name" value={profile?.last_name} />
          <Field label="Email" value={email} />
        </Section>

        <hr style={styles.divider} />

        {/* Contact */}
        <Section title="Contact" onEdit={() => setModal("contact")}>
          <Field label="Phone" value={profile?.phone_number} />
          <Field label="Date of Birth" value={profile?.dob} />
        </Section>

        <hr style={styles.divider} />

        <hr style={styles.divider} />

        {/* Preferences */}
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>Preferences</h2>
          </div>
          <div style={styles.toggleRow}>
            <div>
              <span style={styles.fieldLabel}>Email Notifications</span>
              <span
                style={{
                  ...styles.toggleStatus,
                  color: emailNotifications ? "#16a34a" : "#888",
                }}
              >
                {emailNotifications ? "Enabled" : "Disabled"}
              </span>
            </div>
            <button
              type="button"
              style={{
                ...styles.toggle,
                background: emailNotifications ? "#4f8ef7" : "#ccc",
              }}
              onClick={() => setEmailNotifications((v) => !v)}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: emailNotifications
                    ? "translateX(20px)"
                    : "translateX(0)",
                }}
              />
            </button>
          </div>
          <div style={styles.toggleRow}>
            <div>
              <span style={styles.fieldLabel}>Dark Mode</span>
              <span
                style={{
                  ...styles.toggleStatus,
                  color: darkMode ? "#16a34a" : "#888",
                }}
              >
                {darkMode ? "Enabled" : "Disabled"}
              </span>
            </div>
            <button
              type="button"
              style={{
                ...styles.toggle,
                background: darkMode ? "#4f8ef7" : "#ccc",
              }}
              onClick={() => setDarkMode((v) => !v)}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: darkMode ? "translateX(20px)" : "translateX(0)",
                }}
              />
            </button>
          </div>
        </div>

        <hr style={styles.divider} />

        {/* Security */}
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>Security</h2>
          </div>
          <button
            type="button"
            style={styles.secondaryButton}
            onClick={() => setModal("password")}
          >
            Change Password
          </button>
        </div>
      </div>

      {modal === "password" && (
        <ChangePasswordModal onCancel={() => setModal(null)} />
      )}

      {/* Name edit modal */}
      {modal === "name" && (
        <EditModal
          title="Edit Name"
          fields={[
            {
              name: "first_name",
              label: "First Name",
              value: profile?.first_name || "",
            },
            {
              name: "last_name",
              label: "Last Name",
              value: profile?.last_name || "",
            },
          ]}
          onSave={saveProfile}
          onCancel={() => setModal(null)}
        />
      )}

      {/* Contact edit modal */}
      {modal === "contact" && (
        <EditModal
          title="Edit Contact"
          fields={[
            {
              name: "phone_number",
              label: "Phone",
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
    </div>
  );
}

const styles = {
  page: {
    maxWidth: "720px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: { fontSize: "32px", marginBottom: "8px" },
  subtitle: { color: "var(--text-muted)", marginBottom: "24px" },
  formCard: {
    border: "1px solid var(--border)",
    borderRadius: "12px",
    padding: "24px",
    backgroundColor: "var(--surface)",
    display: "flex",
    flexDirection: "column",
    gap: "0",
  },
  section: { padding: "16px 0" },
  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },
  sectionTitle: { fontSize: "18px", margin: 0, color: "var(--text-strong)" },
  editBtn: {
    padding: "4px 14px",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    background: "none",
    cursor: "pointer",
    fontSize: "14px",
    color: "var(--text)",
  },
  field: {
    display: "flex",
    gap: "16px",
    padding: "6px 0",
    fontSize: "15px",
  },
  fieldLabel: { color: "var(--text-muted)", width: "140px", flexShrink: 0 },
  fieldValue: { color: "var(--text-strong)" },
  divider: {
    border: "none",
    borderTop: "1px solid var(--border-light)",
    margin: 0,
  },
  secondaryButton: {
    padding: "8px 16px",
    borderRadius: "8px",
    border: "1px solid var(--border)",
    cursor: "pointer",
    fontSize: "14px",
    color: "var(--text)",
    background: "none",
  },
  status: { color: "#22c55e", fontSize: "14px", marginBottom: "12px" },
  // Modal
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.6)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modal: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "12px",
    padding: "28px",
    width: "100%",
    maxWidth: "400px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  modalTitle: { margin: 0, fontSize: "18px", color: "var(--text-strong)" },
  modalField: { display: "flex", flexDirection: "column", gap: "4px" },
  modalLabel: { fontSize: "14px", fontWeight: "600", color: "var(--text)" },
  modalInput: {
    padding: "8px 10px",
    borderRadius: "6px",
    border: "1px solid var(--border)",
    fontSize: "14px",
    background: "var(--surface-2)",
    color: "var(--text)",
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
    border: "1px solid var(--border)",
    background: "none",
    cursor: "pointer",
    color: "var(--text)",
  },
  saveBtn: {
    padding: "8px 16px",
    borderRadius: "6px",
    border: "none",
    background: "#4f8ef7",
    color: "#fff",
    cursor: "pointer",
  },
  error: { color: "#ef4444", fontSize: "13px", margin: 0 },
  toggleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 0",
  },
  toggleStatus: { fontSize: "13px", marginLeft: "10px" },
  toggle: {
    width: "44px",
    height: "24px",
    borderRadius: "999px",
    border: "none",
    cursor: "pointer",
    position: "relative",
    flexShrink: 0,
    transition: "background 0.2s",
  },
  toggleKnob: {
    position: "absolute",
    top: "3px",
    left: "3px",
    width: "18px",
    height: "18px",
    borderRadius: "50%",
    background: "#fff",
    transition: "transform 0.2s",
    display: "block",
  },
};

export default Settings;
