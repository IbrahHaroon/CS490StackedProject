import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Document, Page, pdfjs } from "react-pdf";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./DocumentLibrary.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).href;

const DOCUMENT_TYPES = [
  "Resume",
  "Cover Letter",
  "Transcript",
  "Certificate",
  "Other",
];

const STATUS_OPTIONS = ["Draft", "Final", "In Review", "Archived"];

function DocumentLibrary() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [docType, setDocType] = useState(DOCUMENT_TYPES[0]);
  const [docStatus, setDocStatus] = useState("Draft");
  const [docTitle, setDocTitle] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

  // Filtering / sorting (S3-006)
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterIncludeArchived, setFilterIncludeArchived] = useState(false);
  const [sortBy, setSortBy] = useState("updated_desc");

  const [viewingDoc, setViewingDoc] = useState(null);
  const [viewContent, setViewContent] = useState("");
  const [viewFormat, setViewFormat] = useState("");
  const [viewBinaryData, setViewBinaryData] = useState(null);
  const [pdfNumPages, setPdfNumPages] = useState(0);

  const [editingDoc, setEditingDoc] = useState(null);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState("");

  const [genResumeOpen, setGenResumeOpen] = useState(false);
  const [genResumeJobId, setGenResumeJobId] = useState("");
  const [genResumeInstructions, setGenResumeInstructions] = useState("");
  const [genResumeLoading, setGenResumeLoading] = useState(false);
  const [genResumeContent, setGenResumeContent] = useState("");
  const [genResumeDocName, setGenResumeDocName] = useState("");
  const [genResumeError, setGenResumeError] = useState("");

  const [genCoverOpen, setGenCoverOpen] = useState(false);
  const [genCoverJobId, setGenCoverJobId] = useState("");
  const [genCoverInstructions, setGenCoverInstructions] = useState("");
  const [genCoverLoading, setGenCoverLoading] = useState(false);
  const [genCoverContent, setGenCoverContent] = useState("");
  const [genCoverDocName, setGenCoverDocName] = useState("");
  const [genCoverError, setGenCoverError] = useState("");

  const [jobs, setJobs] = useState([]);
  const [deletingId, setDeletingId] = useState(null);
  const fileInputRef = useRef(null);

  const token = localStorage.getItem("token");

  const fetchDocuments = async () => {
    if (!token) {
      setLoadError("You must be signed in to view documents.");
      return;
    }
    try {
      const params = new URLSearchParams();
      if (filterIncludeArchived) params.set("include_archived", "true");
      if (filterType) params.set("document_type", filterType);
      if (filterStatus) params.set("status_filter", filterStatus);
      const url =
        "/documents/me" + (params.toString() ? `?${params.toString()}` : "");
      const res = await api.get(url, {
        caller: "DocumentLibrary.fetchDocuments",
        action: "load_documents",
      });
      if (!res.ok) {
        setLoadError("Failed to load documents. Please sign in again.");
        return;
      }
      const docs = await res.json();
      logAction("DocumentLibrary.fetchDocuments", "documents_loaded", {
        count: docs.length,
      });
      setDocuments(docs);
    } catch (err) {
      setLoadError("Failed to load documents.");
    }
  };

  useEffect(() => {
    fetchDocuments();
    if (token) {
      api
        .get("/jobs/dashboard", {
          caller: "DocumentLibrary.useEffect",
          action: "load_jobs",
        })
        .then((r) => (r.ok ? r.json() : []))
        .then(setJobs)
        .catch(() => setJobs([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, filterType, filterStatus, filterIncludeArchived]);

  // Sorting in JS — backend returns updated_at desc by default
  const sortedDocuments = [...documents].sort((a, b) => {
    if (sortBy === "updated_desc")
      return new Date(b.updated_at) - new Date(a.updated_at);
    if (sortBy === "updated_asc")
      return new Date(a.updated_at) - new Date(b.updated_at);
    if (sortBy === "title_asc")
      return (a.title || "").localeCompare(b.title || "");
    if (sortBy === "title_desc")
      return (b.title || "").localeCompare(a.title || "");
    return 0;
  });

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
    if (docTitle.trim()) form.append("title", docTitle.trim());
    form.append("status_value", docStatus);

    setUploading(true);
    const res = await api.post("/documents/upload", form, {
      caller: "DocumentLibrary.handleUpload",
      action: "upload_document",
    });
    setUploading(false);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setUploadError(err.detail || "Upload failed.");
      return;
    }

    setUploadSuccess("File uploaded successfully.");
    setFile(null);
    setDocTitle("");
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
      const res = await api.get(`/documents/${doc.document_id}/content`, {
        caller: "DocumentLibrary.handleView",
        action: "view_document",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setEditError(err.detail || "Failed to load document content.");
        return;
      }
      const data = await res.json();
      setViewingDoc(doc);
      setViewContent(data.content || "");
      setViewFormat(data.format || "text");
      setViewBinaryData(data.binary_data || null);
      setPdfNumPages(0);
    } catch (err) {
      setEditError("Failed to load document.");
    }
  };

  const handleEdit = async (doc) => {
    setEditError("");
    if (!token) {
      setEditError("You must be signed in to edit documents.");
      return;
    }
    try {
      const res = await api.get(`/documents/${doc.document_id}/content`, {
        caller: "DocumentLibrary.handleEdit",
        action: "load_document_for_edit",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setEditError(err.detail || "Failed to load document content.");
        return;
      }
      const data = await res.json();
      if (!data.editable) {
        setEditError(
          `Cannot edit this file format. Only text-based files (.txt, .md, .docx, .pdf) can be edited.`
        );
        return;
      }
      setEditingDoc(doc);
      setEditContent(data.content || "");
    } catch (err) {
      setEditError("Failed to load document.");
    }
  };

  const handleSave = async () => {
    if (!token) {
      setEditError("You must be signed in to save.");
      return;
    }
    setSaving(true);
    setEditError("");
    // v2: edit content via dedicated /content PUT (creates a new version row)
    const res = await api.put(
      `/documents/${editingDoc.document_id}/content`,
      { content: editContent },
      { caller: "DocumentLibrary.handleSave", action: "save_document_version" }
    );
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

  const handleArchive = async (doc) => {
    const newDeleted = !doc.is_deleted;
    const res = await api.put(
      `/documents/${doc.document_id}`,
      { is_deleted: newDeleted },
      { caller: "DocumentLibrary.handleArchive", action: "archive_document" }
    );
    if (res.ok) {
      setUploadSuccess(newDeleted ? "Document archived." : "Document restored.");
      setTimeout(() => setUploadSuccess(""), 3000);
      fetchDocuments();
    }
  };

  const handleDuplicate = async (doc) => {
    const res = await api.post(
      `/documents/${doc.document_id}/duplicate`,
      {},
      { caller: "DocumentLibrary.handleDuplicate", action: "duplicate_document" }
    );
    if (res.ok) {
      setUploadSuccess("Document duplicated.");
      setTimeout(() => setUploadSuccess(""), 3000);
      fetchDocuments();
    }
  };

  const handleRename = async (doc) => {
    const newTitle = window.prompt("New title:", doc.title);
    if (!newTitle || newTitle === doc.title) return;
    const res = await api.put(
      `/documents/${doc.document_id}`,
      { title: newTitle },
      { caller: "DocumentLibrary.handleRename", action: "rename_document" }
    );
    if (res.ok) {
      setUploadSuccess("Renamed.");
      setTimeout(() => setUploadSuccess(""), 3000);
      fetchDocuments();
    }
  };

  const handleStatusChange = async (doc, newStatus) => {
    const res = await api.put(
      `/documents/${doc.document_id}`,
      { status: newStatus },
      { caller: "DocumentLibrary.handleStatusChange", action: "set_status" }
    );
    if (res.ok) fetchDocuments();
  };

  const handleDelete = async (doc) => {
    if (
      !window.confirm(
        `Permanently delete "${doc.title}"? This cannot be undone. Use Archive to soft-delete instead.`
      )
    )
      return;
    if (!token) return;
    setDeletingId(doc.document_id);
    try {
      const res = await api.delete(`/documents/${doc.document_id}`, {
        caller: "DocumentLibrary.handleDelete",
        action: "delete_document",
      });
      if (!res.ok) {
        let errorMsg = "Failed to delete document.";
        try {
          const err = await res.json();
          errorMsg = err.detail || errorMsg;
        } catch {
          if (res.status === 404)
            errorMsg = "Document not found. It may already be deleted.";
          else if (res.status === 403)
            errorMsg = "You don't have permission to delete this document.";
        }
        setUploadError(errorMsg);
        setTimeout(() => setUploadError(""), 4000);
        setDeletingId(null);
        return;
      }
      setUploadSuccess("Document deleted successfully!");
      setTimeout(() => setUploadSuccess(""), 3000);
      setTimeout(fetchDocuments, 500);
    } catch {
      setUploadError(
        "Network error deleting document. Please check your connection."
      );
      setTimeout(() => setUploadError(""), 4000);
      setDeletingId(null);
    } finally {
      setDeletingId(null);
    }
  };

  const onPdfLoadSuccess = ({ numPages }) => setPdfNumPages(numPages);

  const handleOpenGenResume = () => {
    setGenResumeOpen(true);
    setGenResumeJobId("");
    setGenResumeInstructions("");
    setGenResumeContent("");
    setGenResumeDocName("");
    setGenResumeError("");
  };

  const handleGenResumeGenerate = async () => {
    if (!token) {
      setGenResumeError("You must be signed in.");
      return;
    }
    setGenResumeLoading(true);
    setGenResumeError("");
    try {
      const res = await api.post(
        "/documents/generate-resume",
        {
          job_id: genResumeJobId ? parseInt(genResumeJobId) : null,
          instructions: genResumeInstructions,
        },
        {
          caller: "DocumentLibrary.handleGenResumeGenerate",
          action: "generate_resume",
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setGenResumeError(
          err.detail || "Resume generation failed. Please try again."
        );
        return;
      }
      const data = await res.json();
      setGenResumeContent(data.content);
      setGenResumeDocName(data.title || data.document_name || "");
      fetchDocuments();
    } catch {
      setGenResumeError("Request failed. Check console for details.");
    } finally {
      setGenResumeLoading(false);
    }
  };

  const handleGenResumeClose = () => {
    setGenResumeOpen(false);
    setGenResumeJobId("");
    setGenResumeInstructions("");
    setGenResumeContent("");
    setGenResumeDocName("");
    setGenResumeError("");
  };

  const handleOpenGenCover = () => {
    setGenCoverOpen(true);
    setGenCoverJobId("");
    setGenCoverInstructions("");
    setGenCoverContent("");
    setGenCoverDocName("");
    setGenCoverError("");
  };

  const handleGenCoverGenerate = async () => {
    if (!token) {
      setGenCoverError("You must be signed in.");
      return;
    }
    setGenCoverLoading(true);
    setGenCoverError("");
    try {
      const res = await api.post(
        "/documents/generate-cover-letter",
        {
          job_id: genCoverJobId ? parseInt(genCoverJobId) : null,
          instructions: genCoverInstructions,
        },
        {
          caller: "DocumentLibrary.handleGenCoverGenerate",
          action: "generate_cover_letter",
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setGenCoverError(
          err.detail || "Cover letter generation failed. Please try again."
        );
        return;
      }
      const data = await res.json();
      setGenCoverContent(data.content);
      setGenCoverDocName(data.title || data.document_name || "");
      fetchDocuments();
    } catch {
      setGenCoverError("Request failed. Check console for details.");
    } finally {
      setGenCoverLoading(false);
    }
  };

  const handleGenCoverClose = () => {
    setGenCoverOpen(false);
    setGenCoverJobId("");
    setGenCoverInstructions("");
    setGenCoverContent("");
    setGenCoverDocName("");
    setGenCoverError("");
  };

  return (
    <div className="doclibrary">
      <div className="doclibrary-header">
        <h1>Document Library</h1>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="doclibrary-gen-resume-btn"
            onClick={handleOpenGenResume}
          >
            Generate AI Resume
          </button>
          <button
            className="doclibrary-gen-resume-btn"
            style={{ background: "#a855f7" }}
            onClick={handleOpenGenCover}
          >
            Generate AI Cover Letter
          </button>
        </div>
      </div>

      {viewingDoc && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal">
            <div className="doclibrary-modal-header">
              <h2>View {viewingDoc.title}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setViewingDoc(null);
                  setViewContent("");
                  setViewFormat("");
                  setViewBinaryData(null);
                }}
              >
                ✕
              </button>
            </div>
            <div className="doclibrary-viewer">
              {viewFormat === "pdf" && viewBinaryData ? (
                <Document
                  file={`data:application/pdf;base64,${viewBinaryData}`}
                  onLoadSuccess={onPdfLoadSuccess}
                  className="doclibrary-pdf-document"
                >
                  {Array.from(new Array(pdfNumPages), (_, index) => (
                    <Page key={`page_${index + 1}`} pageNumber={index + 1} />
                  ))}
                </Document>
              ) : viewFormat === "docx" ? (
                <div className="doclibrary-docx-content">
                  <pre>{viewContent}</pre>
                </div>
              ) : (
                <pre>{viewContent}</pre>
              )}
            </div>
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-close-btn"
                onClick={() => {
                  setViewingDoc(null);
                  setViewContent("");
                  setViewFormat("");
                  setViewBinaryData(null);
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
              <h2>Edit {editingDoc.title}</h2>
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
              placeholder="Edit your document content here..."
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
                {saving ? "Saving..." : "Save as new version"}
              </button>
            </div>
          </div>
        </div>
      )}

      {genResumeOpen && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal doclibrary-ai-modal">
            <div className="doclibrary-modal-header">
              <h2>Generate AI Resume</h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleGenResumeClose}
              >
                ✕
              </button>
            </div>
            {!genResumeContent && (
              <div className="doclibrary-ai-prompt">
                <label className="doclibrary-ai-label">
                  Target Job{" "}
                  <span className="doclibrary-ai-optional">(optional)</span>
                </label>
                <select
                  className="doclibrary-gen-select"
                  value={genResumeJobId}
                  onChange={(e) => setGenResumeJobId(e.target.value)}
                  disabled={genResumeLoading}
                >
                  <option value="">— General resume (no specific job) —</option>
                  {jobs.map((job) => (
                    <option key={job.job_id} value={job.job_id}>
                      {job.title} @ {job.company_name} ({job.stage})
                    </option>
                  ))}
                </select>

                <label
                  className="doclibrary-ai-label"
                  style={{ marginTop: "0.75rem" }}
                >
                  Additional Instructions{" "}
                  <span className="doclibrary-ai-optional">(optional)</span>
                </label>
                <textarea
                  className="doclibrary-ai-instructions"
                  value={genResumeInstructions}
                  onChange={(e) => setGenResumeInstructions(e.target.value)}
                  placeholder="e.g. Emphasize backend experience, target a senior-level role…"
                  rows={3}
                  disabled={genResumeLoading}
                />
                {genResumeError && (
                  <p className="doclibrary-error">{genResumeError}</p>
                )}
              </div>
            )}
            {genResumeLoading && (
              <div className="doclibrary-ai-loading">
                <div className="doclibrary-ai-spinner" />
                <p>Generating your resume…</p>
              </div>
            )}
            {genResumeContent && !genResumeLoading && (
              <div className="doclibrary-gen-result">
                <div className="doclibrary-gen-result-header">
                  <span className="doclibrary-gen-saved-badge">
                    Saved as &ldquo;{genResumeDocName}&rdquo;
                  </span>
                </div>
                <textarea
                  className="doclibrary-gen-textarea"
                  value={genResumeContent}
                  readOnly
                />
              </div>
            )}
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={handleGenResumeClose}
              >
                {genResumeContent ? "Close" : "Cancel"}
              </button>
              {!genResumeContent && (
                <button
                  className="doclibrary-ai-generate-btn"
                  onClick={handleGenResumeGenerate}
                  disabled={genResumeLoading}
                >
                  {genResumeLoading ? "Generating…" : "Generate Resume"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {genCoverOpen && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal doclibrary-ai-modal">
            <div className="doclibrary-modal-header">
              <h2>Generate AI Cover Letter</h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleGenCoverClose}
              >
                ✕
              </button>
            </div>
            {!genCoverContent && (
              <div className="doclibrary-ai-prompt">
                <label className="doclibrary-ai-label">
                  Target Job{" "}
                  <span className="doclibrary-ai-optional">(optional)</span>
                </label>
                <select
                  className="doclibrary-gen-select"
                  value={genCoverJobId}
                  onChange={(e) => setGenCoverJobId(e.target.value)}
                  disabled={genCoverLoading}
                >
                  <option value="">
                    — General cover letter (no specific job) —
                  </option>
                  {jobs.map((job) => (
                    <option key={job.job_id} value={job.job_id}>
                      {job.title} @ {job.company_name} ({job.stage})
                    </option>
                  ))}
                </select>

                <label
                  className="doclibrary-ai-label"
                  style={{ marginTop: "0.75rem" }}
                >
                  Additional Instructions{" "}
                  <span className="doclibrary-ai-optional">(optional)</span>
                </label>
                <textarea
                  className="doclibrary-ai-instructions"
                  value={genCoverInstructions}
                  onChange={(e) => setGenCoverInstructions(e.target.value)}
                  placeholder="e.g. Emphasize leadership experience, formal tone…"
                  rows={3}
                  disabled={genCoverLoading}
                />
                {genCoverError && (
                  <p className="doclibrary-error">{genCoverError}</p>
                )}
              </div>
            )}
            {genCoverLoading && (
              <div className="doclibrary-ai-loading">
                <div className="doclibrary-ai-spinner" />
                <p>Generating your cover letter…</p>
              </div>
            )}
            {genCoverContent && !genCoverLoading && (
              <div className="doclibrary-gen-result">
                <div className="doclibrary-gen-result-header">
                  <span className="doclibrary-gen-saved-badge">
                    Saved as &ldquo;{genCoverDocName}&rdquo;
                  </span>
                </div>
                <textarea
                  className="doclibrary-gen-textarea"
                  value={genCoverContent}
                  readOnly
                />
              </div>
            )}
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={handleGenCoverClose}
              >
                {genCoverContent ? "Close" : "Cancel"}
              </button>
              {!genCoverContent && (
                <button
                  className="doclibrary-ai-generate-btn"
                  onClick={handleGenCoverGenerate}
                  disabled={genCoverLoading}
                >
                  {genCoverLoading ? "Generating…" : "Generate Cover Letter"}
                </button>
              )}
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

          <label>Title (optional)</label>
          <input
            type="text"
            value={docTitle}
            onChange={(e) => setDocTitle(e.target.value)}
            placeholder="Defaults to filename"
          />

          <label>Status</label>
          <select
            value={docStatus}
            onChange={(e) => setDocStatus(e.target.value)}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
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
        <div
          style={{
            display: "flex",
            gap: "12px",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
          }}
        >
          <h2>Your Documents</h2>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              title="Filter by type"
            >
              <option value="">All types</option>
              {DOCUMENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              title="Filter by status"
            >
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              title="Sort"
            >
              <option value="updated_desc">Newest first</option>
              <option value="updated_asc">Oldest first</option>
              <option value="title_asc">Title A→Z</option>
              <option value="title_desc">Title Z→A</option>
            </select>
            <label
              style={{ display: "flex", alignItems: "center", gap: "4px" }}
            >
              <input
                type="checkbox"
                checked={filterIncludeArchived}
                onChange={(e) => setFilterIncludeArchived(e.target.checked)}
              />
              Show archived
            </label>
          </div>
        </div>
        {loadError && <p className="doclibrary-error">{loadError}</p>}
        {!loadError && sortedDocuments.length === 0 && (
          <p className="doclibrary-empty">No documents.</p>
        )}
        {sortedDocuments.length > 0 && (
          <table className="doclibrary-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Status</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedDocuments.map((doc) => (
                <tr key={doc.document_id} style={doc.is_deleted ? { opacity: 0.5 } : {}}>
                  <td>{doc.title}</td>
                  <td>{doc.document_type}</td>
                  <td>
                    <select
                      value={doc.status}
                      onChange={(e) => handleStatusChange(doc, e.target.value)}
                      style={{ padding: "2px 4px" }}
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    {doc.updated_at
                      ? new Date(doc.updated_at).toLocaleDateString()
                      : "—"}
                  </td>
                  <td>
                    <div className="doclibrary-actions">
                      <button
                        className="doclibrary-action-btn doclibrary-view-btn"
                        onClick={() => handleView(doc)}
                        disabled={deletingId !== null}
                        title="View Document"
                      >
                        View
                      </button>
                      <button
                        className="doclibrary-action-btn doclibrary-edit-btn"
                        onClick={() => handleEdit(doc)}
                        disabled={deletingId !== null}
                        title="Edit content (creates a new version)"
                      >
                        Edit
                      </button>
                      <button
                        className="doclibrary-action-btn"
                        onClick={() => handleRename(doc)}
                        disabled={deletingId !== null}
                        title="Rename"
                      >
                        Rename
                      </button>
                      <button
                        className="doclibrary-action-btn"
                        onClick={() => handleDuplicate(doc)}
                        disabled={deletingId !== null}
                        title="Duplicate"
                      >
                        Duplicate
                      </button>
                      <button
                        className="doclibrary-action-btn"
                        onClick={() => handleArchive(doc)}
                        disabled={deletingId !== null}
                        title={doc.is_deleted ? "Restore" : "Archive"}
                      >
                        {doc.is_deleted ? "Restore" : "Archive"}
                      </button>
                      <button
                        className="doclibrary-action-btn doclibrary-delete-btn"
                        onClick={() => handleDelete(doc)}
                        disabled={deletingId === doc.document_id}
                        title="Permanently delete"
                      >
                        {deletingId === doc.document_id
                          ? "Deleting…"
                          : "Delete"}
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
