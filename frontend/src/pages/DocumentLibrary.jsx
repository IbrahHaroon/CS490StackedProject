import { useEffect, useRef, useState } from "react";
import "./DocumentLibrary.css";

const API = "http://localhost:8000";

const DOCUMENT_TYPES = [
  "Resume",
  "Cover Letter",
  "Transcript",
  "Certificate",
  "Other",
];

function DocumentLibrary() {
  const [documents, setDocuments] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [docType, setDocType] = useState(DOCUMENT_TYPES[0]);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [confirmDoc, setConfirmDoc] = useState(null); // doc to delete
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const fileInputRef = useRef(null);

  const token = localStorage.getItem("token");

  const fetchDocuments = async () => {
    if (!token) {
      setLoadError("You must be signed in to view documents.");
      return;
    }
    const res = await fetch(`${API}/documents/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      setLoadError("Failed to load documents. Please sign in again.");
      return;
    }
    setDocuments(await res.json());
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    setUploadError("");
    setUploadSuccess("");

    if (!file) {
      setUploadError("Please select a file.");
      return;
    }
    if (!token) {
      setUploadError("You must be signed in to upload.");
      return;
    }

    const form = new FormData();
    form.append("file", file);
    form.append("document_type", docType);

    setUploading(true);
    try {
      const res = await fetch(`${API}/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });

      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/signin";
        return;
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setUploadError(err.detail || `Upload failed (${res.status}).`);
        return;
      }

      setUploadSuccess("File uploaded successfully.");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      fetchDocuments();
    } catch (err) {
      setUploadError("Cannot reach the server. Make sure the backend is running.");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!confirmDoc) return;
    setDeleteError("");
    setDeleting(true);
    try {
      const res = await fetch(`${API}/documents/${confirmDoc.doc_id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/signin";
        return;
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setDeleteError(err.detail || "Failed to delete document.");
        return;
      }

      setConfirmDoc(null);
      fetchDocuments();
    } catch (err) {
      setDeleteError("Cannot reach the server.");
    } finally {
      setDeleting(false);
    }
  };

  const docName = (doc) =>
    doc.document_name ||
    (doc.document_location ? doc.document_location.split("/").pop() : "Unnamed");

  return (
    <div className="doclibrary">
      <h1>Document Library</h1>

      <section className="doclibrary-upload">
        <h2>Upload Document</h2>
        <form onSubmit={handleUpload} className="doclibrary-upload-form">
          <label>Document Type</label>
          <select value={docType} onChange={(e) => setDocType(e.target.value)}>
            {DOCUMENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>

          <label>File</label>
          <input
            ref={fileInputRef}
            type="file"
            onChange={(e) => setFile(e.target.files[0] || null)}
            required
          />

          {uploadError && <p className="doclibrary-error">{uploadError}</p>}
          {uploadSuccess && (
            <p className="doclibrary-success">{uploadSuccess}</p>
          )}

          <button
            type="submit"
            className="doclibrary-upload-btn"
            disabled={uploading}
          >
            {uploading ? "Uploading…" : "Upload"}
          </button>
        </form>
      </section>

      <section className="doclibrary-list">
        <h2>Your Documents</h2>
        {loadError && <p className="doclibrary-error">{loadError}</p>}
        {!loadError && documents.length === 0 && (
          <p className="doclibrary-empty">No documents uploaded yet.</p>
        )}
        {documents.length > 0 && (
          <table className="doclibrary-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.doc_id}>
                  <td>{docName(doc)}</td>
                  <td>{doc.document_type}</td>
                  <td>
                    <span className="doclibrary-confirmed">✓ In System</span>
                  </td>
                  <td>
                    <button
                      className="doclibrary-delete-btn"
                      onClick={() => { setDeleteError(""); setConfirmDoc(doc); }}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {confirmDoc && (
        <div className="doclibrary-overlay">
          <div className="doclibrary-modal">
            <h3 className="doclibrary-modal-title">Remove Document</h3>
            <p className="doclibrary-modal-body">
              Are you sure you want to remove <strong>{docName(confirmDoc)}</strong>? This
              cannot be undone.
            </p>
            {deleteError && <p className="doclibrary-error">{deleteError}</p>}
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-modal-cancel"
                onClick={() => setConfirmDoc(null)}
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                className="doclibrary-modal-confirm"
                onClick={handleDeleteConfirm}
                disabled={deleting}
              >
                {deleting ? "Removing…" : "Remove"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentLibrary;
