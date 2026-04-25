export default function DeleteConfirmModal({
  isOpen,
  title = "Delete application?",
  message = "This action cannot be undone.",
  onCancel,
  onConfirm,
  isDeleting = false,
}) {
  if (!isOpen) return null;

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <h3 style={styles.title}>{title}</h3>
        <p style={styles.message}>{message}</p>

        <div style={styles.actions}>
          <button
            style={styles.cancelBtn}
            onClick={onCancel}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            style={styles.deleteBtn}
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
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
    background: "rgba(0,0,0,0.45)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modal: {
    width: "100%",
    maxWidth: "420px",
    background: "#151a33",
    color: "white",
    border: "1px solid #394264",
    borderRadius: "14px",
    padding: "24px",
    boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
  },
  title: {
    margin: "0 0 12px 0",
    fontSize: "22px",
  },
  message: {
    margin: "0 0 20px 0",
    color: "#c7cbe0",
    lineHeight: 1.5,
  },
  actions: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "10px",
  },
  cancelBtn: {
    padding: "10px 16px",
    borderRadius: "10px",
    border: "1px solid #394264",
    background: "transparent",
    color: "white",
    cursor: "pointer",
  },
  deleteBtn: {
    padding: "10px 16px",
    borderRadius: "10px",
    border: "none",
    background: "#dc3545",
    color: "white",
    cursor: "pointer",
  },
};
