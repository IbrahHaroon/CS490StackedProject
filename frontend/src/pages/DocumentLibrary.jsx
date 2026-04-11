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
  const [viewingDoc, setViewingDoc] = useState(null);
  const [viewContent, setViewContent] = useState("");
  const [editingDoc, setEditingDoc] = useState(null);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState("");
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

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

  const handleView = async (doc) => {
    setEditError("");
    if (!token) {
      setEditError("You must be signed in to view documents.");
      return;
    }

    try {
      const res = await fetch(`${API}/documents/${doc.doc_id}/content`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setEditError(err.detail || "Failed to load document content.");
        return;
      }

      const data = await res.json();
      setViewingDoc(doc);
      setViewContent(data.content || "");
    } catch (err) {
      console.error("Error:", err);
      setEditError("Failed to load document. Check console for details.");
    }
  };

  const handleEdit = async (doc) => {
    setEditError("");
    if (!token) {
      setEditError("You must be signed in to edit documents.");
      return;
    }

    try {
      const res = await fetch(`${API}/documents/${doc.doc_id}/content`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setEditError(err.detail || "Failed to load document content.");
        return;
      }

      const data = await res.json();
      if (data.source === "binary") {
        setEditError(
          `Cannot edit binary file: ${data.filename}. Only text-based resumes can be edited.`
        );
        return;
      }

      setEditingDoc(doc);
      setEditContent(data.content || "");
    } catch (err) {
      console.error("Error:", err);
      setEditError("Failed to load document. Check console for details.");
    }
  };

  const handleSave = async () => {
    if (!token) {
      setEditError("You must be signed in to save.");
      return;
    }

    setSaving(true);
    setEditError("");
    const res = await fetch(`${API}/documents/${editingDoc.doc_id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content: editContent }),
    });
    setSaving(false);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setEditError(err.detail || "Failed to save document.");
      return;
    }

    setEditingDoc(null);
    setEditContent("");
    setUploadSuccess("Document saved successfully!");
    setTimeout(() => setUploadSuccess(""), 3000);
    fetchDocuments();
  };

  const handleDelete = async (doc) => {
    if (!window.confirm(`Delete ${doc.document_name}?`)) {
      return;
    }

    if (!token) {
      setEditError("You must be signed in to delete.");
      return;
    }

    const res = await fetch(`${API}/documents/${doc.doc_id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setEditError(err.detail || "Failed to delete document.");
      return;
    }

    setUploadSuccess("Document deleted successfully!");
    setTimeout(() => setUploadSuccess(""), 3000);
    fetchDocuments();
  };

  return (
    <div className="doclibrary">
      <h1>Document Library</h1>

      {viewingDoc && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal">
            <div className="doclibrary-modal-header">
              <h2>View {viewingDoc.document_name}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setViewingDoc(null);
                  setViewContent("");
                }}
              >
                ✕
              </button>
            </div>

            <div className="doclibrary-viewer">
              <pre>{viewContent}</pre>
            </div>

            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-close-btn"
                onClick={() => {
                  setViewingDoc(null);
                  setViewContent("");
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {editingDoc && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal">
            <div className="doclibrary-modal-header">
              <h2>Edit {editingDoc.document_name}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setEditingDoc(null);
                  setEditContent("");
                  setEditError("");
                }}
              >
                ✕
              </button>
            </div>

            {editError && <p className="doclibrary-error">{editError}</p>}

            <textarea
              className="doclibrary-editor"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              placeholder="Edit your resume content here..."
            />

            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={() => {
                  setEditingDoc(null);
                  setEditContent("");
                  setEditError("");
                }}
              >
                Cancel
              </button>
              <button
                className="doclibrary-save-btn"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}

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
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.doc_id}>
                  <td>
                    {doc.document_name ||
                      doc.document_location.split("/").pop()}
                  </td>
                  <td>{doc.document_type}</td>
                  <td>
                    <span className="doclibrary-confirmed">✓ In System</span>
                  </td>
                  <td>
                    <div className="doclibrary-actions">
                      <button
                        className="doclibrary-action-btn doclibrary-view-btn"
                        onClick={() => handleView(doc)}
                        title="View Resume"
                      >
                        View
                      </button>
                      <button
                        className="doclibrary-action-btn doclibrary-edit-btn"
                        onClick={() => handleEdit(doc)}
                        title="Edit Resume"
                      >
                        Edit
                      </button>
                      <button
                        className="doclibrary-action-btn doclibrary-delete-btn"
                        onClick={() => handleDelete(doc)}
                        title="Delete Resume"
                      >
                        Delete
                      </button>
                    </div>
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
