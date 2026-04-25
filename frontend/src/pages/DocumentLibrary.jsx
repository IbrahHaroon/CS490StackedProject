import { useEffect, useMemo, useRef, useState } from "react";
import "./DocumentLibrary.css";

const API = "http://localhost:8000";

const DOCUMENT_TYPES = ["Resume", "Cover Letter", "Transcript", "Certificate", "Other"];
const STATUS_FILTERS = ["All", "In System", "Archived"];
const SORT_OPTIONS = [
  { value: "newest", label: "Newest updated" },
  { value: "oldest", label: "Oldest updated" },
  { value: "name", label: "Name A-Z" },
  { value: "type", label: "Type A-Z" },
];

function getDocumentName(doc) {
  return (
    doc.title ||
    doc.name ||
    doc.file_name ||
    doc.filename ||
    doc.document_location?.split("/").pop() ||
    "Untitled Document"
  );
}

function getDocumentStatus(doc) {
  if (doc.archived || doc.is_archived) return "Archived";
  return doc.status || "In System";
}

function getDocumentUpdatedDate(doc) {
  return doc.updated_at || doc.modified_at || doc.created_at || doc.uploaded_at || "";
}

function getDocumentTags(doc) {
  if (Array.isArray(doc.tags)) return doc.tags;
  if (typeof doc.tags === "string") {
    return doc.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
  }
  return [];
}

function DocumentLibrary() {
  const [documents, setDocuments] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [docType, setDocType] = useState(DOCUMENT_TYPES[0]);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [tagFilter, setTagFilter] = useState("All");
  const [sortBy, setSortBy] = useState("newest");

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
    setLoadError("");
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const availableTags = useMemo(() => {
    const tags = documents.flatMap((doc) => getDocumentTags(doc));
    return ["All", ...new Set(tags)];
  }, [documents]);

  const filteredDocuments = useMemo(() => {
    const query = search.toLowerCase().trim();

    return [...documents]
      .filter((doc) => {
        const name = getDocumentName(doc);
        const status = getDocumentStatus(doc);
        const tags = getDocumentTags(doc);
        const updatedDate = getDocumentUpdatedDate(doc);

        const matchesSearch =
          query === "" ||
          name.toLowerCase().includes(query) ||
          doc.document_type?.toLowerCase().includes(query) ||
          status.toLowerCase().includes(query) ||
          tags.some((tag) => tag.toLowerCase().includes(query));

        const matchesType = typeFilter === "All" || doc.document_type === typeFilter;
        const matchesStatus = statusFilter === "All" || status === statusFilter;
        const matchesTag = tagFilter === "All" || tags.includes(tagFilter);

        return matchesSearch && matchesType && matchesStatus && matchesTag;
      })
      .sort((a, b) => {
        const nameA = getDocumentName(a).toLowerCase();
        const nameB = getDocumentName(b).toLowerCase();
        const typeA = a.document_type || "";
        const typeB = b.document_type || "";
        const dateA = new Date(getDocumentUpdatedDate(a) || 0);
        const dateB = new Date(getDocumentUpdatedDate(b) || 0);

        if (sortBy === "oldest") return dateA - dateB;
        if (sortBy === "name") return nameA.localeCompare(nameB);
        if (sortBy === "type") return typeA.localeCompare(typeB);
        return dateB - dateA;
      });
  }, [documents, search, typeFilter, statusFilter, tagFilter, sortBy]);

  const clearFilters = () => {
    setSearch("");
    setTypeFilter("All");
    setStatusFilter("All");
    setTagFilter("All");
    setSortBy("newest");
  };

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
          {uploadSuccess && <p className="doclibrary-success">{uploadSuccess}</p>}

          <button type="submit" className="doclibrary-upload-btn" disabled={uploading}>
            {uploading ? "Uploading…" : "Upload"}
          </button>
        </form>
      </section>

      <section className="doclibrary-list">
        <div className="doclibrary-list-header">
          <div>
            <h2>Your Documents</h2>
            <p className="doclibrary-helper">
              Search, filter, and sort your uploaded documents.
            </p>
          </div>

          <span className="doclibrary-count">
            {filteredDocuments.length} of {documents.length} shown
          </span>
        </div>

        <div className="doclibrary-controls">
          <input
            type="text"
            placeholder="Search documents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="doclibrary-search"
          />

          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="All">All Types</option>
            {DOCUMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            {STATUS_FILTERS.map((status) => (
              <option key={status} value={status}>
                {status === "All" ? "All Statuses" : status}
              </option>
            ))}
          </select>

          <select value={tagFilter} onChange={(e) => setTagFilter(e.target.value)}>
            {availableTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag === "All" ? "All Tags" : tag}
              </option>
            ))}
          </select>

          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                Sort: {option.label}
              </option>
            ))}
          </select>

          <button type="button" className="doclibrary-clear-btn" onClick={clearFilters}>
            Clear
          </button>
        </div>

        {loadError && <p className="doclibrary-error">{loadError}</p>}

        {!loadError && documents.length === 0 && (
          <p className="doclibrary-empty">No documents uploaded yet.</p>
        )}

        {!loadError && documents.length > 0 && filteredDocuments.length === 0 && (
          <p className="doclibrary-empty">No documents match your filters.</p>
        )}

        {filteredDocuments.length > 0 && (
          <table className="doclibrary-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Tags</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map((doc) => {
                const tags = getDocumentTags(doc);
                const updatedDate = getDocumentUpdatedDate(doc);

                return (
                  <tr key={doc.doc_id}>
                    <td>{getDocumentName(doc)}</td>
                    <td>{doc.document_type || "Other"}</td>
                    <td>
                      <span
                        className={
                          getDocumentStatus(doc) === "Archived"
                            ? "doclibrary-archived"
                            : "doclibrary-confirmed"
                        }
                      >
                        {getDocumentStatus(doc) === "Archived"
                          ? "Archived"
                          : "✓ In System"}
                      </span>
                    </td>
                    <td>
                      <div className="doclibrary-tags">
                        {tags.length > 0 ? (
                          tags.map((tag) => (
                            <span key={tag} className="doclibrary-tag">
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="doclibrary-muted">No tags</span>
                        )}
                      </div>
                    </td>
                    <td>
                      {updatedDate ? (
                        new Date(updatedDate).toLocaleDateString()
                      ) : (
                        <span className="doclibrary-muted">Unknown</span>
                      )}
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