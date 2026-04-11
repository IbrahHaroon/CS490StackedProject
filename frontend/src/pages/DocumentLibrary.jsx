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
    const res = await fetch(`${API}/documents/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    setUploading(false);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setUploadError(err.detail || "Upload failed.");
      return;
    }

    setUploadSuccess("File uploaded successfully.");
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    fetchDocuments();
  };

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
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.doc_id}>
                  <td>{doc.document_location.split("/").pop()}</td>
                  <td>{doc.document_type}</td>
                  <td>
                    <span className="doclibrary-confirmed">✓ In System</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default DocumentLibrary;
