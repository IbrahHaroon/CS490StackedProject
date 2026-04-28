import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./DocumentLibrary.css";

const DOCUMENT_TYPES = [
  "Resume",
  "Cover Letter",
  "Transcript",
  "Certificate",
  "Other",
];

const STATUS_OPTIONS = ["Draft", "Final", "In Review", "Archived"];

function formatResumeContent(text) {
  const lines = text.split("\n");
  const elements = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      elements.push(<div key={`empty-${i}`} style={{ height: "0.5rem" }} />);
      continue;
    }

    // ALL CAPS section headers (EXPERIENCE, EDUCATION, SKILLS, etc.)
    if (
      trimmed === trimmed.toUpperCase() &&
      trimmed.length > 2 &&
      /[A-Z]/.test(trimmed)
    ) {
      elements.push(
        <div
          key={`header-${i}`}
          style={{
            fontSize: "1.1rem",
            fontWeight: "bold",
            marginTop: "1rem",
            marginBottom: "0.5rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#000",
          }}
        >
          {trimmed}
        </div>
      );
      continue;
    }

    // Bullet points
    if (/^[-•*]\s/.test(trimmed)) {
      const content = trimmed.slice(2);
      elements.push(
        <div
          key={`bullet-${i}`}
          style={{
            marginLeft: "1.5rem",
            marginBottom: "0.4rem",
            lineHeight: "1.5",
          }}
        >
          <span style={{ marginRight: "0.5rem" }}>•</span>
          {content}
        </div>
      );
      continue;
    }

    // Job title/company line (contains company name in different formatting)
    if (
      (trimmed.includes("@") ||
        trimmed.includes(" - ") ||
        /^\w+.*[A-Z]{2,}.*\d{4}/.test(trimmed)) &&
      trimmed.length > 5
    ) {
      // Make company names and dates bold
      let formatted = trimmed
        .replace(/(@|–|—|\|)(.*?)($|@|–|—|\|)/g, (match) => {
          return `<strong>${match}</strong>`;
        })
        .replace(/\b\d{4}\b/g, (match) => {
          return `<strong>${match}</strong>`;
        });

      elements.push(
        <div
          key={`company-${i}`}
          style={{
            fontWeight: "500",
            marginTop: "0.6rem",
            marginBottom: "0.3rem",
            lineHeight: "1.5",
          }}
          dangerouslySetInnerHTML={{ __html: formatted }}
        />
      );
      continue;
    }

    // Name/title at the very top (first non-empty line, all letters/spaces)
    if (
      i === 0 ||
      (i < 3 && elements.length < 2 && /^[A-Za-z\s]+$/.test(trimmed))
    ) {
      elements.push(
        <div
          key={`name-${i}`}
          style={{
            fontSize: "1.3rem",
            fontWeight: "bold",
            marginBottom: "0.3rem",
            color: "#000",
          }}
        >
          {trimmed}
        </div>
      );
      continue;
    }

    // Contact info line (emails, phone, links)
    if (
      trimmed.includes("@") ||
      trimmed.includes("linkedin") ||
      /\(\d{3}\)|\d{3}-\d{4}/.test(trimmed)
    ) {
      elements.push(
        <div
          key={`contact-${i}`}
          style={{
            fontSize: "0.9rem",
            marginBottom: "0.3rem",
            color: "#333",
            lineHeight: "1.5",
          }}
        >
          {trimmed}
        </div>
      );
      continue;
    }

    // Default text
    elements.push(
      <div
        key={`text-${i}`}
        style={{
          marginBottom: "0.4rem",
          lineHeight: "1.5",
          color: "#000",
        }}
      >
        {trimmed}
      </div>
    );
  }

  return elements;
}

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

  const [viewingDoc, setViewingDoc] = useState(null);
  const [viewContent, setViewContent] = useState("");
  const [viewFormat, setViewFormat] = useState("");
  const [viewBinaryData, setViewBinaryData] = useState(null);

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

  // Filtering / sorting (S3-006)
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterIncludeArchived, setFilterIncludeArchived] = useState(false);
  const [sortBy, setSortBy] = useState("updated_desc");
  const [filterTag, setFilterTag] = useState("");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");

  const [jobs, setJobs] = useState([]);
  const [docJobMap, setDocJobMap] = useState({});
  const [deletingId, setDeletingId] = useState(null);
  const [deleteConfirmDoc, setDeleteConfirmDoc] = useState(null);
  const [renameDoc, setRenameDoc] = useState(null);
  const [renamingId, setRenamingId] = useState(null);
  const [newTitle, setNewTitle] = useState("");

  // S3-003: version history modal
  const [historyDoc, setHistoryDoc] = useState(null);
  const [versions, setVersions] = useState([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [restoringVersionId, setRestoringVersionId] = useState(null);
  const [viewingVersion, setViewingVersion] = useState(null);
  const [versionContent, setVersionContent] = useState("");

  const fileInputRef = useRef(null);

  const token = localStorage.getItem("token");

  const formattedResumeContent = useMemo(
    () => formatResumeContent(viewContent),
    [viewContent]
  );

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
      if (filterTag) params.set("tag_filter", filterTag);
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
      api
        .get("/documents/links/me", {
          caller: "DocumentLibrary.useEffect",
          action: "load_doc_links",
        })
        .then((r) => (r.ok ? r.json() : []))
        .then((links) => {
          const map = {};
          for (const l of links) {
            if (!map[l.document_id]) map[l.document_id] = [];
            if (!map[l.document_id].some((x) => x.job_id === l.job_id)) {
              map[l.document_id].push({
                job_id: l.job_id,
                job_title: l.job_title,
                company_name: l.company_name,
              });
            }
          }
          setDocJobMap(map);
        })
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, filterType, filterStatus, filterIncludeArchived, filterTag]);

  // Derive unique tags from all documents
  const allTags = useMemo(() => {
    const set = new Set();
    documents.forEach((d) => (d.tags || []).forEach((t) => set.add(t)));
    return [...set].sort();
  }, [documents]);

  // Sorting and date filtering in JS
  const sortedDocuments = useMemo(() => {
    let list = [...documents];

    // Date range filtering
    if (filterDateFrom) {
      list = list.filter(
        (d) => new Date(d.updated_at) >= new Date(filterDateFrom)
      );
    }
    if (filterDateTo) {
      list = list.filter(
        (d) => new Date(d.updated_at) <= new Date(filterDateTo + "T23:59:59")
      );
    }

    // Sorting
    list.sort((a, b) => {
      if (sortBy === "updated_desc")
        return new Date(b.updated_at) - new Date(a.updated_at);
      if (sortBy === "updated_asc")
        return new Date(a.updated_at) - new Date(b.updated_at);
      if (sortBy === "title_asc")
        return (a.title || "").localeCompare(b.title || "");
      if (sortBy === "title_desc")
        return (b.title || "").localeCompare(a.title || "");
      if (sortBy === "type_asc")
        return (a.document_type || "").localeCompare(b.document_type || "");
      if (sortBy === "status_asc")
        return (a.status || "").localeCompare(b.status || "");
      return 0;
    });

    return list;
  }, [documents, sortBy, filterDateFrom, filterDateTo]);

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
      setUploadSuccess(
        newDeleted ? "Document archived." : "Document restored."
      );
      setTimeout(() => setUploadSuccess(""), 3000);
      fetchDocuments();
    }
  };

  const handleDuplicate = async (doc) => {
    const res = await api.post(
      `/documents/${doc.document_id}/duplicate`,
      {},
      {
        caller: "DocumentLibrary.handleDuplicate",
        action: "duplicate_document",
      }
    );
    if (res.ok) {
      setUploadSuccess("Document duplicated.");
      setTimeout(() => setUploadSuccess(""), 3000);
      fetchDocuments();
    }
  };

  const handleDownload = async (doc) => {
    try {
      const res = await api.get(`/documents/${doc.document_id}/download`, {
        caller: "DocumentLibrary.handleDownload",
        action: "download_document",
      });
      if (!res.ok) {
        setEditError("Failed to download document.");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const fileName = doc.title.endsWith(".docx")
        ? doc.title
        : `${doc.title}.docx`;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setEditError("Failed to download document.");
    }
  };

  const handleDownloadVersion = async (doc, versionId) => {
    try {
      const res = await api.get(
        `/documents/${doc.document_id}/versions/${versionId}/download`,
        {
          caller: "DocumentLibrary.handleDownloadVersion",
          action: "download_document_version",
        }
      );
      if (!res.ok) {
        setEditError("Failed to download version.");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const fileName = doc.title.endsWith(".docx")
        ? doc.title
        : `${doc.title}.docx`;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setEditError("Failed to download version.");
    }
  };

  const handleRenameClick = (doc) => {
    setRenameDoc(doc);
    setNewTitle(doc.title);
  };

  const handleConfirmRename = async () => {
    if (!renameDoc || !newTitle || newTitle === renameDoc.title) {
      setRenameDoc(null);
      setNewTitle("");
      return;
    }
    setRenamingId(renameDoc.document_id);
    try {
      const res = await api.put(
        `/documents/${renameDoc.document_id}`,
        { title: newTitle },
        { caller: "DocumentLibrary.handleRename", action: "rename_document" }
      );
      if (res.ok) {
        setUploadSuccess("Renamed.");
        setTimeout(() => setUploadSuccess(""), 3000);
        fetchDocuments();
      }
    } finally {
      setRenamingId(null);
      setRenameDoc(null);
      setNewTitle("");
    }
  };

  const handleCancelRename = () => {
    setRenameDoc(null);
    setNewTitle("");
  };

  const handleStatusChange = async (doc, newStatus) => {
    const res = await api.put(
      `/documents/${doc.document_id}`,
      { status: newStatus },
      { caller: "DocumentLibrary.handleStatusChange", action: "set_status" }
    );
    if (res.ok) fetchDocuments();
  };

  // S3-003: open the version-history modal for a document and load its versions.
  const handleOpenHistory = async (doc) => {
    setHistoryDoc(doc);
    setVersions([]);
    setVersionsLoading(true);
    try {
      const res = await api.get(`/documents/${doc.document_id}/versions`, {
        caller: "DocumentLibrary.handleOpenHistory",
        action: "load_document_versions",
      });
      if (res.ok) setVersions(await res.json());
    } catch {
      // leave versions empty; modal will show "No versions yet."
    }
    setVersionsLoading(false);
  };

  // S3-003: fetch the content of a specific (non-current) version and open
  // the nested viewer modal.
  const handleViewVersion = async (version) => {
    if (!historyDoc) return;
    try {
      const res = await api.get(
        `/documents/${historyDoc.document_id}/versions/${version.version_id}/content`,
        {
          caller: "DocumentLibrary.handleViewVersion",
          action: "view_document_version",
        }
      );
      if (!res.ok) return;
      const data = await res.json();
      setVersionContent(data.content || "");
      setViewingVersion(version);
    } catch {
      // silently ignore — user can retry
    }
  };

  // S3-003: restore an older version as the current one. Confirms first,
  // then refreshes both the modal's history doc and the underlying list.
  const handleRestoreVersion = async (version) => {
    if (!historyDoc) return;
    if (
      !window.confirm(
        `Restore v${version.version_number} as the current version?`
      )
    )
      return;
    setRestoringVersionId(version.version_id);
    try {
      const res = await api.post(
        `/documents/${historyDoc.document_id}/versions/${version.version_id}/restore`,
        {},
        {
          caller: "DocumentLibrary.handleRestoreVersion",
          action: "restore_document_version",
        }
      );
      if (res.ok) {
        const updated = await res.json();
        setHistoryDoc(updated);
        fetchDocuments();
      }
    } catch {
      // silently ignore — user can retry
    }
    setRestoringVersionId(null);
  };

  const handleDeleteClick = (doc) => {
    setDeleteConfirmDoc(doc);
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmDoc || !token) {
      setDeleteConfirmDoc(null);
      return;
    }
    setDeletingId(deleteConfirmDoc.document_id);
    try {
      const res = await api.delete(
        `/documents/${deleteConfirmDoc.document_id}`,
        {
          caller: "DocumentLibrary.handleDelete",
          action: "delete_document",
        }
      );
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
        setDeleteConfirmDoc(null);
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
      setDeleteConfirmDoc(null);
    }
  };

  const handleCancelDelete = () => {
    setDeleteConfirmDoc(null);
  };

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

      // Auto-download the generated DOCX
      const downloadRes = await api.get(
        `/documents/${data.document_id}/versions/${data.version_id}/download`,
        {
          caller: "DocumentLibrary.handleGenResumeGenerate",
          action: "download_generated_resume",
        }
      );
      if (downloadRes.ok) {
        const blob = await downloadRes.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${data.title || "resume"}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }
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

      // Auto-download the generated DOCX
      const downloadRes = await api.get(
        `/documents/${data.document_id}/versions/${data.version_id}/download`,
        {
          caller: "DocumentLibrary.handleGenCoverGenerate",
          action: "download_generated_cover_letter",
        }
      );
      if (downloadRes.ok) {
        const blob = await downloadRes.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${data.title || "cover_letter"}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }
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
          <div
            className="doclibrary-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="doc-view-title"
          >
            <div className="doclibrary-modal-header">
              <h2 id="doc-view-title">View {viewingDoc.title}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setViewingDoc(null);
                  setViewContent("");
                  setViewFormat("");
                  setViewBinaryData(null);
                }}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div className="doclibrary-viewer">
              {viewFormat === "pdf" && viewBinaryData ? (
                <iframe
                  src={`data:application/pdf;base64,${viewBinaryData}`}
                  title={viewingDoc?.title}
                  style={{
                    width: "100%",
                    height: "100%",
                    border: "none",
                    minHeight: "520px",
                  }}
                />
              ) : viewFormat === "docx" ? (
                <div className="doclibrary-docx-content">
                  <pre>{viewContent}</pre>
                </div>
              ) : viewingDoc?.document_type === "Resume" ? (
                <div className="doclibrary-resume-content">
                  {formattedResumeContent}
                </div>
              ) : (
                <pre>{viewContent}</pre>
              )}
            </div>
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-download-btn"
                onClick={() => handleDownload(viewingDoc)}
              >
                Download
              </button>
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
          <div
            className="doclibrary-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="doc-edit-title"
          >
            <div className="doclibrary-modal-header">
              <h2 id="doc-edit-title">Edit {editingDoc.title}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setEditingDoc(null);
                  setEditContent("");
                  setEditError("");
                }}
                aria-label="Close"
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
          <div
            className="doclibrary-modal doclibrary-ai-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="gen-resume-title"
          >
            <div className="doclibrary-modal-header">
              <h2 id="gen-resume-title">Generate AI Resume</h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleGenResumeClose}
                aria-label="Close"
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
          <div
            className="doclibrary-modal doclibrary-ai-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="gen-cover-title"
          >
            <div className="doclibrary-modal-header">
              <h2 id="gen-cover-title">Generate AI Cover Letter</h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleGenCoverClose}
                aria-label="Close"
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

      {renameDoc && (
        <div className="doclibrary-modal-overlay">
          <div
            className="doclibrary-modal"
            style={{ maxWidth: "400px" }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="rename-doc-title"
          >
            <div className="doclibrary-modal-header">
              <h2 style={{ margin: 0 }} id="rename-doc-title">
                Rename Document
              </h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleCancelRename}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div style={{ padding: "1.5rem", borderTop: "1px solid #e5e7eb" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "0.5rem",
                  fontSize: "0.9rem",
                  fontWeight: "500",
                }}
              >
                New title:
              </label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleConfirmRename();
                  if (e.key === "Escape") handleCancelRename();
                }}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  marginBottom: "1rem",
                  border: "1px solid #d1d5db",
                  borderRadius: "0.375rem",
                  fontSize: "0.95rem",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={handleCancelRename}
              >
                Cancel
              </button>
              <button
                className="doclibrary-save-btn"
                onClick={handleConfirmRename}
                disabled={
                  renamingId === renameDoc.document_id ||
                  !newTitle ||
                  newTitle === renameDoc.title
                }
              >
                {renamingId === renameDoc.document_id ? "Renaming…" : "Rename"}
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteConfirmDoc && (
        <div className="doclibrary-modal-overlay">
          <div
            className="doclibrary-modal"
            style={{ maxWidth: "400px" }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-doc-title"
          >
            <div className="doclibrary-modal-header">
              <h2 style={{ margin: 0, color: "#ef4444" }} id="delete-doc-title">
                Delete Document
              </h2>
              <button
                className="doclibrary-modal-close"
                onClick={handleCancelDelete}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div style={{ padding: "1.5rem", borderTop: "1px solid #e5e7eb" }}>
              <p style={{ margin: "0 0 0.75rem 0", fontSize: "0.95rem" }}>
                Are you sure you want to permanently delete:
              </p>
              <p
                style={{
                  margin: "0 0 1.5rem 0",
                  padding: "0.75rem",
                  background: "#fef2f2",
                  borderRadius: "0.375rem",
                  fontSize: "0.9rem",
                  fontWeight: "500",
                  color: "#7f1d1d",
                  wordBreak: "break-word",
                }}
              >
                {deleteConfirmDoc.title}
              </p>
              <p style={{ margin: "0", fontSize: "0.85rem", color: "#6b7280" }}>
                This action cannot be undone. Consider using Archive instead to
                soft-delete.
              </p>
            </div>
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={handleCancelDelete}
              >
                Cancel
              </button>
              <button
                className="doclibrary-delete-btn"
                onClick={handleConfirmDelete}
                disabled={deletingId === deleteConfirmDoc.document_id}
                style={{
                  background: "#ef4444",
                  color: "white",
                  border: "none",
                  padding: "0.5rem 1rem",
                  borderRadius: "0.375rem",
                  cursor: "pointer",
                  fontWeight: "500",
                }}
              >
                {deletingId === deleteConfirmDoc.document_id
                  ? "Deleting…"
                  : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* S3-003: Version history modal */}
      {historyDoc && (
        <div className="doclibrary-modal-overlay">
          <div
            className="doclibrary-modal"
            style={{ maxWidth: "640px" }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="history-title"
          >
            <div className="doclibrary-modal-header">
              <h2 id="history-title">Version history — {historyDoc.title}</h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => setHistoryDoc(null)}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            {versionsLoading ? (
              <p style={{ padding: "1rem" }}>Loading…</p>
            ) : versions.length === 0 ? (
              <p style={{ padding: "1rem" }}>No versions yet.</p>
            ) : (
              <table className="doclibrary-table" style={{ marginTop: 0 }}>
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Source</th>
                    <th>Saved</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {versions.map((v) => {
                    const isCurrent =
                      v.version_id === historyDoc.current_version_id;
                    return (
                      <tr key={v.version_id}>
                        <td>
                          v{v.version_number}
                          {isCurrent && (
                            <span style={{ marginLeft: 6, color: "#22c55e" }}>
                              · current
                            </span>
                          )}
                        </td>
                        <td>{v.source || "—"}</td>
                        <td>{new Date(v.created_at).toLocaleString()}</td>
                        <td>
                          <div className="doclibrary-actions">
                            <button
                              className="doclibrary-action-btn doclibrary-view-btn"
                              onClick={() => handleViewVersion(v)}
                            >
                              View
                            </button>
                            <button
                              className="doclibrary-action-btn"
                              onClick={() =>
                                handleDownloadVersion(historyDoc, v.version_id)
                              }
                            >
                              Download
                            </button>
                            {!isCurrent && (
                              <button
                                className="doclibrary-action-btn"
                                onClick={() => handleRestoreVersion(v)}
                                disabled={restoringVersionId === v.version_id}
                              >
                                {restoringVersionId === v.version_id
                                  ? "Restoring…"
                                  : "Restore"}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-cancel-btn"
                onClick={() => setHistoryDoc(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* S3-003: nested viewer for a specific version's content */}
      {viewingVersion && (
        <div className="doclibrary-modal-overlay">
          <div className="doclibrary-modal">
            <div className="doclibrary-modal-header">
              <h2>
                v{viewingVersion.version_number} —{" "}
                {historyDoc ? historyDoc.title : ""}
              </h2>
              <button
                className="doclibrary-modal-close"
                onClick={() => {
                  setViewingVersion(null);
                  setVersionContent("");
                }}
              >
                ✕
              </button>
            </div>
            <div className="doclibrary-viewer">
              <pre>{versionContent}</pre>
            </div>
            <div className="doclibrary-modal-actions">
              <button
                className="doclibrary-download-btn"
                onClick={() =>
                  handleDownloadVersion(historyDoc, viewingVersion.version_id)
                }
              >
                Download
              </button>
              <button
                className="doclibrary-close-btn"
                onClick={() => {
                  setViewingVersion(null);
                  setVersionContent("");
                }}
              >
                Close
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
          <div className="doclibrary-filters">
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
              value={filterTag}
              onChange={(e) => setFilterTag(e.target.value)}
              title="Filter by tag"
            >
              <option value="">All tags</option>
              {allTags.map((t) => (
                <option key={t} value={t}>
                  {t}
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
              <option value="type_asc">Type A→Z</option>
              <option value="status_asc">Status A→Z</option>
            </select>
            <input
              type="date"
              value={filterDateFrom}
              onChange={(e) => setFilterDateFrom(e.target.value)}
              title="Updated from"
            />
            <input
              type="date"
              value={filterDateTo}
              onChange={(e) => setFilterDateTo(e.target.value)}
              title="Updated to"
            />
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                color: "#000000",
              }}
            >
              <input
                type="checkbox"
                checked={filterIncludeArchived}
                onChange={(e) => setFilterIncludeArchived(e.target.checked)}
              />
              Show archived
            </label>
            <button
              className="doclibrary-clear-filters-btn"
              onClick={() => {
                setFilterType("");
                setFilterStatus("");
                setFilterTag("");
                setFilterDateFrom("");
                setFilterDateTo("");
                setSortBy("updated_desc");
              }}
            >
              Clear filters
            </button>
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
              {sortedDocuments.map((doc) => {
                const linkedJobs = docJobMap[doc.document_id] || [];
                return (
                  <tr
                    key={doc.document_id}
                    style={doc.is_deleted ? { opacity: 0.5 } : {}}
                  >
                    <td>
                      <div>{doc.title}</div>
                      {linkedJobs.length > 0 && (
                        <div
                          style={{
                            marginTop: "4px",
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "4px",
                          }}
                        >
                          {linkedJobs.map((lj) => (
                            <button
                              key={lj.job_id}
                              onClick={() =>
                                navigate(`/applications?job=${lj.job_id}`)
                              }
                              title={`Go to ${lj.job_title} @ ${lj.company_name}`}
                              style={{
                                background: "none",
                                border: "1px solid #4f8ef7",
                                borderRadius: "4px",
                                color: "#4f8ef7",
                                cursor: "pointer",
                                fontSize: "0.72rem",
                                padding: "1px 6px",
                                whiteSpace: "nowrap",
                              }}
                            >
                              → {lj.job_title} @ {lj.company_name}
                            </button>
                          ))}
                        </div>
                      )}
                      {(doc.tags || []).length > 0 && (
                        <div
                          style={{
                            marginTop: "4px",
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "4px",
                          }}
                        >
                          {doc.tags.map((tag) => (
                            <button
                              key={tag}
                              className="doclibrary-tag-pill"
                              onClick={() =>
                                setFilterTag(tag === filterTag ? "" : tag)
                              }
                              title={
                                filterTag === tag
                                  ? "Clear tag filter"
                                  : `Filter by "${tag}"`
                              }
                            >
                              {tag}
                            </button>
                          ))}
                        </div>
                      )}
                    </td>
                    <td>{doc.document_type}</td>
                    <td>
                      <select
                        value={doc.status}
                        onChange={(e) =>
                          handleStatusChange(doc, e.target.value)
                        }
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
                          onClick={() => handleRenameClick(doc)}
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
                          className="doclibrary-action-btn"
                          onClick={() => handleOpenHistory(doc)}
                          disabled={deletingId !== null}
                          title="View version history"
                        >
                          History
                        </button>
                        <button
                          className="doclibrary-action-btn doclibrary-delete-btn"
                          onClick={() => handleDeleteClick(doc)}
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
