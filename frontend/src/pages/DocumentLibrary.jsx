import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Document, Page, pdfjs } from "react-pdf";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./DocumentLibrary.css";

// Set up PDF.js worker
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

function DocumentLibrary() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [docType, setDocType] = useState(DOCUMENT_TYPES[0]);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [viewingDoc, setViewingDoc] = useState(null);
  const [viewContent, setViewContent] = useState("");
  const [viewFormat, setViewFormat] = useState("");
  const [viewBinaryData, setViewBinaryData] = useState(null);
  const [viewEditable, setViewEditable] = useState(false);
  const [editingDoc, setEditingDoc] = useState(null);
  const [editContent, setEditContent] = useState("");
  const [editFormat, setEditFormat] = useState("");
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState("");
  const [pdfNumPages, setPdfNumPages] = useState(0);
  const [aiDoc, setAiDoc] = useState(null);
  const [aiInstructions, setAiInstructions] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiOriginal, setAiOriginal] = useState("");
  const [aiImproved, setAiImproved] = useState("");
  const [aiError, setAiError] = useState("");
  const [aiApplying, setAiApplying] = useState(false);
  const [genResumeOpen, setGenResumeOpen] = useState(false);
  const [genResumeJobId, setGenResumeJobId] = useState("");
  const [genResumeInstructions, setGenResumeInstructions] = useState("");
  const [genResumeLoading, setGenResumeLoading] = useState(false);
  const [genResumeContent, setGenResumeContent] = useState("");
  const [genResumeDocName, setGenResumeDocName] = useState("");
  const [genResumeError, setGenResumeError] = useState("");
  const [appliedJobs, setAppliedJobs] = useState([]);
  const [positions, setPositions] = useState([]);
  const [genCoverOpen, setGenCoverOpen] = useState(false);
  const [genCoverJobId, setGenCoverJobId] = useState("");
  const [genCoverInstructions, setGenCoverInstructions] = useState("");
  const [genCoverLoading, setGenCoverLoading] = useState(false);
  const [genCoverContent, setGenCoverContent] = useState("");
  const [genCoverDocName, setGenCoverDocName] = useState("");
  const [genCoverError, setGenCoverError] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const fileInputRef = useRef(null);

  const token = localStorage.getItem("token");

  const fetchDocuments = async () => {
    if (!token) {
      setLoadError("You must be signed in to view documents.");
      return;
    }
    try {
      const res = await api.get("/documents/me", { caller: "DocumentLibrary.fetchDocuments", action: "load_documents" });
      if (!res.ok) {
        setLoadError("Failed to load documents. Please sign in again.");
        return;
      }
      const docs = await res.json();
      logAction("DocumentLibrary.fetchDocuments", "documents_loaded", { count: docs.length });
      setDocuments(docs);
    } catch (err) {
      logAction("DocumentLibrary.fetchDocuments", "load_documents_error", { error: err.message });
      setLoadError("Failed to load documents.");
    }
  };

  useEffect(() => {
    fetchDocuments();
    if (token) {
      Promise.all([
        api.get("/jobs/dashboard", { caller: "DocumentLibrary.useEffect", action: "load_applied_jobs" }),
        api.get("/jobs/positions/?include_manual=true", { caller: "DocumentLibrary.useEffect", action: "load_positions" }),
      ]).then(([jobsRes, posRes]) => {
        if (jobsRes.ok) jobsRes.json().then(setAppliedJobs);
        if (posRes.ok) posRes.json().then(setPositions);
      });
    }
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
    const res = await api.post("/documents/upload", form, { caller: "DocumentLibrary.handleUpload", action: "upload_document" });
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
      const res = await api.get(`/documents/${doc.doc_id}/content`, { caller: "DocumentLibrary.handleView", action: "view_document" });

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
      setViewEditable(data.editable || false);
      setPdfNumPages(0);
    } catch (err) {
      logAction("DocumentLibrary.handleView", "view_document_error", { error: err.message });
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
      const res = await api.get(`/documents/${doc.doc_id}/content`, { caller: "DocumentLibrary.handleEdit", action: "load_document_for_edit" });

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
      setEditFormat(data.format || "text");
    } catch (err) {
      logAction("DocumentLibrary.handleEdit", "edit_document_error", { error: err.message });
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
    const res = await api.put(`/documents/${editingDoc.doc_id}`, { content: editContent }, { caller: "DocumentLibrary.handleSave", action: "save_document" });
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
      setUploadError("You must be signed in to delete.");
      setTimeout(() => setUploadError(""), 3000);
      return;
    }

    logAction("DocumentLibrary.handleDelete", "delete_document_attempt", { doc_id: doc.doc_id, name: doc.document_name });
    setDeletingId(doc.doc_id);
    try {
      const res = await api.delete(`/documents/${doc.doc_id}`, { caller: "DocumentLibrary.handleDelete", action: "delete_document" });

      if (!res.ok) {
        let errorMsg = "Failed to delete document.";
        let responseBody = "";
        try {
          responseBody = await res.text();
          const err = JSON.parse(responseBody);
          errorMsg = err.detail || errorMsg;
          logAction("DocumentLibrary.handleDelete", "delete_error", { doc_id: doc.doc_id, detail: err.detail });
        } catch (e) {
          if (res.status === 404) {
            errorMsg = "Document not found. It may have already been deleted.";
          } else if (res.status === 403) {
            errorMsg = "You don't have permission to delete this document.";
          }
          logAction("DocumentLibrary.handleDelete", "delete_error_unparsed", { status: res.status });
        }
        setUploadError(errorMsg);
        setTimeout(() => setUploadError(""), 4000);
        setDeletingId(null);
        return;
      }

      logAction("DocumentLibrary.handleDelete", "delete_success", { doc_id: doc.doc_id });
      setUploadSuccess("Document deleted successfully!");
      setTimeout(() => setUploadSuccess(""), 3000);
      // Refresh documents after a short delay to ensure backend processed
      setTimeout(() => {
        fetchDocuments();
      }, 500);
    } catch (err) {
      logAction("DocumentLibrary.handleDelete", "delete_network_error", { error: err.message });
      setUploadError(
        "Network error deleting document. Please check your connection."
      );
      setTimeout(() => setUploadError(""), 4000);
      setDeletingId(null);
    } finally {
      setDeletingId(null);
    }
  };

  const onPdfLoadSuccess = ({ numPages }) => {
    setPdfNumPages(numPages);
  };

  const handleAiImprove = (doc) => {
    setAiDoc(doc);
    setAiInstructions("");
    setAiOriginal("");
    setAiImproved("");
    setAiError("");
  };

  const handleAiGenerate = async () => {
    if (!token) {
      setAiError("You must be signed in.");
      return;
    }
    setAiLoading(true);
    setAiError("");
    setAiOriginal("");
    setAiImproved("");

    try {
      const res = await api.post(`/documents/${aiDoc.doc_id}/ai-rewrite`, { instructions: aiInstructions }, { caller: "DocumentLibrary.handleAiGenerate", action: "ai_rewrite" });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiError(err.detail || "AI rewrite failed. Please try again.");
        return;
      }

      const data = await res.json();
      setAiOriginal(data.original);
      setAiImproved(data.improved);
    } catch (err) {
      logAction("DocumentLibrary.handleAiGenerate", "ai_rewrite_error", { error: err.message });
      setAiError("Request failed.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleAiApply = async () => {
    if (!token || !aiDoc) return;
    setAiApplying(true);
    setAiError("");

    const res = await api.put(`/documents/${aiDoc.doc_id}`, { content: aiImproved }, { caller: "DocumentLibrary.handleAiApply", action: "apply_ai_improvements" });
    setAiApplying(false);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setAiError(err.detail || "Failed to apply changes.");
      return;
    }

    setAiDoc(null);
    setUploadSuccess("AI improvements applied successfully!");
    setTimeout(() => setUploadSuccess(""), 3000);
    fetchDocuments();
  };

  const handleAiClose = () => {
    setAiDoc(null);
    setAiInstructions("");
    setAiOriginal("");
    setAiImproved("");
    setAiError("");
  };

  const handleOpenGenResume = async () => {
    setGenResumeOpen(true);
    setGenResumeJobId("");
    setGenResumeInstructions("");
    setGenResumeContent("");
    setGenResumeDocName("");
    setGenResumeError("");

    try {
      const [jobsRes, posRes] = await Promise.all([
        api.get("/jobs/dashboard", { caller: "DocumentLibrary.handleOpenGenResume", action: "load_applied_jobs" }),
        api.get("/jobs/positions/", { caller: "DocumentLibrary.handleOpenGenResume", action: "load_positions" }),
      ]);
      if (jobsRes.ok) setAppliedJobs(await jobsRes.json());
      if (posRes.ok) setPositions(await posRes.json());
    } catch {
      // dropdown will just be empty; not fatal
    }
  };

  const handleGenResumeGenerate = async () => {
    if (!token) {
      setGenResumeError("You must be signed in.");
      return;
    }
    setGenResumeLoading(true);
    setGenResumeError("");

    try {
      const res = await api.post("/documents/generate-resume", {
          job_id: genResumeJobId ? parseInt(genResumeJobId) : null,
          instructions: genResumeInstructions,
        }, { caller: "DocumentLibrary.handleGenResumeGenerate", action: "generate_resume" });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setGenResumeError(
          err.detail || "Resume generation failed. Please try again."
        );
        return;
      }

      const data = await res.json();
      setGenResumeContent(data.content);
      setGenResumeDocName(data.document_name);
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

  const handleOpenGenCover = async () => {
    setGenCoverOpen(true);
    setGenCoverJobId("");
    setGenCoverInstructions("");
    setGenCoverContent("");
    setGenCoverDocName("");
    setGenCoverError("");

    try {
      const [jobsRes, posRes] = await Promise.all([
        api.get("/jobs/dashboard", { caller: "DocumentLibrary.handleOpenGenCover", action: "load_applied_jobs" }),
        api.get("/jobs/positions/", { caller: "DocumentLibrary.handleOpenGenCover", action: "load_positions" }),
      ]);
      if (jobsRes.ok) setAppliedJobs(await jobsRes.json());
      if (posRes.ok) setPositions(await posRes.json());
    } catch {
      // dropdown will just be empty; not fatal
    }
  };

  const handleGenCoverGenerate = async () => {
    if (!token) {
      setGenCoverError("You must be signed in.");
      return;
    }
    setGenCoverLoading(true);
    setGenCoverError("");

    try {
      const res = await api.post("/documents/generate-cover-letter", {
          job_id: genCoverJobId ? parseInt(genCoverJobId) : null,
          instructions: genCoverInstructions,
        }, { caller: "DocumentLibrary.handleGenCoverGenerate", action: "generate_cover_letter" });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setGenCoverError(
          err.detail || "Cover letter generation failed. Please try again."
        );
        return;
      }

      const data = await res.json();
      setGenCoverContent(data.content);
      setGenCoverDocName(data.document_name);
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

  // Build a position lookup map for the job dropdown
  const positionMap = Object.fromEntries(
    positions.map((p) => [p.position_id, p])
  );

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
              <h2>View {viewingDoc.document_name}</h2>
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
              <h2>Edit {editingDoc.document_name}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setEditingDoc(null);
                  setEditContent("");
                  setEditFormat("");
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
              disabled={!viewEditable}
            />

            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={() => {
                  setEditingDoc(null);
                  setEditContent("");
                  setEditFormat("");
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

      {aiDoc && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal doclibrary-ai-modal">
            <div className="doclibrary-modal-header">
              <h2>AI Improve — {aiDoc.document_name}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleAiClose}
              >
                ✕
              </button>
            </div>

            {!aiOriginal && (
              <div className="doclibrary-ai-prompt">
                <label className="doclibrary-ai-label">
                  Instructions{" "}
                  <span className="doclibrary-ai-optional">(optional)</span>
                </label>
                <textarea
                  className="doclibrary-ai-instructions"
                  value={aiInstructions}
                  onChange={(e) => setAiInstructions(e.target.value)}
                  placeholder="e.g. Make it more ATS-friendly, strengthen action verbs, tailor for a software engineering role…"
                  rows={3}
                  disabled={aiLoading}
                />
                {aiError && <p className="doclibrary-error">{aiError}</p>}
              </div>
            )}

            {aiLoading && (
              <div className="doclibrary-ai-loading">
                <div className="doclibrary-ai-spinner" />
                <p>Generating improvements…</p>
              </div>
            )}

            {aiOriginal && !aiLoading && (
              <div className="doclibrary-ai-compare">
                <div className="doclibrary-ai-col">
                  <div className="doclibrary-ai-col-header">Original</div>
                  <pre className="doclibrary-ai-text">{aiOriginal}</pre>
                </div>
                <div className="doclibrary-ai-col">
                  <div className="doclibrary-ai-col-header doclibrary-ai-col-header--improved">
                    AI Suggestion
                  </div>
                  <textarea
                    className="doclibrary-ai-text doclibrary-ai-text--editable"
                    value={aiImproved}
                    onChange={(e) => setAiImproved(e.target.value)}
                  />
                </div>
              </div>
            )}

            {aiError && aiOriginal && (
              <p className="doclibrary-error doclibrary-ai-error-inline">
                {aiError}
              </p>
            )}

            <div className="doclibrary-modal-actions">
              <button className="doclibrary-cancel-btn" onClick={handleAiClose}>
                Cancel
              </button>
              {!aiOriginal && (
                <button
                  className="doclibrary-ai-generate-btn"
                  onClick={handleAiGenerate}
                  disabled={aiLoading}
                >
                  {aiLoading ? "Generating…" : "Generate Improvements"}
                </button>
              )}
              {aiOriginal && (
                <>
                  <button
                    className="doclibrary-cancel-btn"
                    onClick={() => {
                      setAiOriginal("");
                      setAiImproved("");
                      setAiError("");
                    }}
                  >
                    Try Again
                  </button>
                  <button
                    className="doclibrary-save-btn"
                    onClick={handleAiApply}
                    disabled={aiApplying}
                  >
                    {aiApplying ? "Applying…" : "Apply Changes"}
                  </button>
                </>
              )}
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
                  {appliedJobs.map((job) => {
                    const pos = positionMap[job.position_id];
                    const label = pos
                      ? `${pos.title} at ${pos.company_name} (${job.application_status})`
                      : `Application #${job.job_id} (${job.application_status})`;
                    return (
                      <option key={job.job_id} value={job.job_id}>
                        {label}
                      </option>
                    );
                  })}
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
                  placeholder="e.g. Emphasize backend experience, target a senior-level role, keep to one page…"
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
                  {appliedJobs.map((job) => {
                    const pos = positionMap[job.position_id];
                    const label = pos
                      ? `${pos.title} at ${pos.company_name} (${job.application_status})`
                      : `Application #${job.job_id} (${job.application_status})`;
                    return (
                      <option key={job.job_id} value={job.job_id}>
                        {label}
                      </option>
                    );
                  })}
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
                  placeholder="e.g. Emphasize leadership experience, keep it under one page, formal tone…"
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
                <th>Linked Job</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => {
                const linkedJob = doc.job_id
                  ? appliedJobs.find((j) => j.job_id === doc.job_id)
                  : null;
                const linkedPos = linkedJob
                  ? positionMap[linkedJob.position_id]
                  : null;
                const jobLabel = linkedPos
                  ? `${linkedPos.title} @ ${linkedPos.company_name}`
                  : null;
                return (
                  <tr key={doc.doc_id}>
                    <td>
                      {doc.document_name ||
                        doc.document_location.split("/").pop()}
                    </td>
                    <td>{doc.document_type}</td>
                    <td>
                      {jobLabel && linkedPos ? (
                        <button
                          className="doclibrary-linked-job doclibrary-linked-job-btn"
                          onClick={() =>
                            navigate(`/?job=${linkedPos.position_id}`)
                          }
                          title="Open job card in Dashboard"
                        >
                          {jobLabel}
                        </button>
                      ) : (
                        <span className="doclibrary-unlinked">—</span>
                      )}
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
                          title="Edit Document"
                        >
                          Edit
                        </button>
                        <button
                          className="doclibrary-action-btn doclibrary-ai-btn"
                          onClick={() => handleAiImprove(doc)}
                          disabled={deletingId !== null}
                          title="AI Improve"
                        >
                          AI Improve
                        </button>
                        <button
                          className="doclibrary-action-btn doclibrary-delete-btn"
                          onClick={() => handleDelete(doc)}
                          disabled={deletingId === doc.doc_id}
                          title="Delete Document"
                        >
                          {deletingId === doc.doc_id ? "Deleting…" : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default DocumentLibrary;
