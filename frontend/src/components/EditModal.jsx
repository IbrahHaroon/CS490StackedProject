import { useState } from "react";

/**
 * Generic edit modal used across Profile, Settings, and other pages.
 *
 * Props:
 *   title    — string, modal heading
 *   fields   — array of { name, label, value, type?, placeholder?, maxLength? }
 *              Supported types: "text" (default), "date", "textarea"
 *   onSave   — async (values) => null | errorString
 *              Return null on success; return an error string to display in the modal.
 *   onCancel — () => void
 */
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
                maxLength={f.maxLength}
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

const styles = {
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
    maxWidth: "420px",
    maxHeight: "80vh",
    overflowY: "auto",
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

export default EditModal;
