import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import DemoBanner from "../components/common/DemoBanner";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import { isMockApiEnabled, knowledgeService } from "../services";
import { getUserFacingError } from "../utils/errors";
import { formatBytes, formatDateTime } from "../utils/format";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];
const ACCEPTED_TYPES = new Set(["pdf", "docx", "txt"]);
const POLL_MS = 4000;

function fileExtension(name) {
  const parts = String(name || "").toLowerCase().split(".");
  return parts.length > 1 ? parts.pop() : "";
}

function isSupportedFile(file) {
  if (!file) return false;
  return ACCEPTED_TYPES.has(fileExtension(file.name));
}

function documentId(doc) {
  return doc?.id || doc?.document_id || "";
}

export default function KnowledgePage() {
  const [status, setStatus] = useState("loading");
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);
  const pollRef = useRef(null);

  const processing = useMemo(
    () => documents.some((item) => String(item.status).toUpperCase() === "PROCESSING"),
    [documents]
  );

  const loadDocuments = useCallback(async ({ silent = false } = {}) => {
    if (!silent) {
      setStatus("loading");
      setError("");
    }
    try {
      const data = await knowledgeService.listDocuments();
      setDocuments(Array.isArray(data) ? data : []);
      setStatus("ready");
    } catch (err) {
      setError(getUserFacingError(err, "Could not load knowledge documents."));
      if (!silent) setStatus("error");
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    if (!processing || status !== "ready") return undefined;
    pollRef.current = window.setInterval(() => {
      loadDocuments({ silent: true });
    }, POLL_MS);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [processing, status, loadDocuments]);

  function chooseFile(file) {
    setUploadError("");
    setUploadSuccess("");
    setDeleteError("");
    if (!file) {
      setSelectedFile(null);
      return;
    }
    if (!isSupportedFile(file)) {
      setSelectedFile(null);
      setUploadError("Supported file types are PDF, DOCX, and TXT.");
      return;
    }
    setSelectedFile(file);
  }

  async function onUpload(event) {
    event.preventDefault();
    if (!selectedFile) {
      setUploadError("Select a PDF, DOCX, or TXT file first.");
      return;
    }
    if (!isSupportedFile(selectedFile)) {
      setUploadError("Supported file types are PDF, DOCX, and TXT.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setUploading(true);
    setUploadError("");
    setUploadSuccess("");
    try {
      const result = await knowledgeService.uploadDocument(formData);
      const filename = result?.filename || selectedFile.name;
      const uploadStatus = result?.status || "PROCESSING";
      setUploadSuccess(`${filename} uploaded. Status: ${uploadStatus}.`);
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = "";
      await loadDocuments({ silent: true });
      setStatus("ready");
    } catch (err) {
      setUploadError(getUserFacingError(err, "Could not upload that document."));
    } finally {
      setUploading(false);
    }
  }

  async function onDelete(doc) {
    const id = documentId(doc);
    if (!id) return;
    const confirmed = window.confirm(`Delete “${doc.filename || id}”? This cannot be undone.`);
    if (!confirmed) return;

    setDeletingId(id);
    setDeleteError("");
    try {
      await knowledgeService.deleteDocument(id);
      await loadDocuments({ silent: true });
      setStatus("ready");
    } catch (err) {
      setDeleteError(getUserFacingError(err, "Could not delete that document."));
    } finally {
      setDeletingId("");
    }
  }

  return (
    <section className="page-stack">
      <PageHeader
        title="Knowledge Base"
        description="Upload brand and marketing documents so workflows can use them as context. Files are stored and processed through the knowledge API (PDF, DOCX, TXT)."
        actions={
          <button type="button" className="btn btn-secondary" onClick={() => loadDocuments()} disabled={status === "loading"}>
            Refresh
          </button>
        }
      />

      {isMockApiEnabled ? (
        <DemoBanner text="Demo knowledge documents — mock API data, not live processed files." />
      ) : null}

      {status === "loading" ? <LoadingState message="Loading documents..." /> : null}
      {status === "error" ? <ErrorState message={error} onRetry={() => loadDocuments()} /> : null}

      {status === "ready" ? (
        <>
          <section className="page-card">
            <h2>Upload a document</h2>
            <p className="muted">
              Accepted types: PDF, DOCX, TXT. The backend extracts, chunks, and embeds the file. Processing status is
              refreshed from the document list.
            </p>
            {uploadError ? <p className="error-text">{uploadError}</p> : null}
            {uploadSuccess ? <p className="success-text">{uploadSuccess}</p> : null}
            <form className="stack-form" onSubmit={onUpload}>
              <div
                className={`dropzone${dragOver ? " is-over" : ""}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragOver(false);
                  chooseFile(event.dataTransfer.files?.[0]);
                }}
              >
                <label htmlFor="knowledge-file" className="dropzone-label">
                  Drop a file here or choose one
                </label>
                <input
                  ref={inputRef}
                  id="knowledge-file"
                  type="file"
                  accept={ACCEPTED_EXTENSIONS.join(",")}
                  onChange={(event) => chooseFile(event.target.files?.[0] || null)}
                />
              </div>

              {selectedFile ? (
                <dl className="meta-list">
                  <dt>Selected file</dt>
                  <dd>{selectedFile.name}</dd>
                  <dt>Type</dt>
                  <dd>{fileExtension(selectedFile.name).toUpperCase() || "—"}</dd>
                  <dt>Size</dt>
                  <dd>{formatBytes(selectedFile.size)}</dd>
                </dl>
              ) : (
                <p className="muted">No file selected.</p>
              )}

              <div className="form-actions">
                <button type="submit" className="btn" disabled={uploading || !selectedFile}>
                  {uploading ? "Uploading..." : "Upload document"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={uploading || !selectedFile}
                  onClick={() => {
                    setSelectedFile(null);
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                >
                  Clear
                </button>
              </div>
            </form>
          </section>

          {deleteError ? <p className="error-text">{deleteError}</p> : null}

          {documents.length === 0 ? (
            <div className="page-card">
              <EmptyState
                title="No documents yet"
                description="Upload a PDF, DOCX, or TXT file to start building the knowledge base."
              />
            </div>
          ) : (
            <div className="table-wrap page-card">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Status</th>
                    <th>Uploaded</th>
                    <th>Notes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => {
                    const id = documentId(doc);
                    const note = doc.error || doc.message || doc.processing_error || "";
                    return (
                      <tr key={id || doc.filename}>
                        <td>{doc.filename || doc.name || "Untitled"}</td>
                        <td>{doc.type || fileExtension(doc.filename).toUpperCase() || "—"}</td>
                        <td>{formatBytes(doc.size ?? doc.size_bytes ?? doc.file_size)}</td>
                        <td>
                          <StatusBadge status={doc.status} />
                        </td>
                        <td>{formatDateTime(doc.uploaded_at || doc.created_at)}</td>
                        <td>{note || (String(doc.status).toUpperCase() === "PROCESSING" ? "Processing via API list refresh" : "—")}</td>
                        <td>
                          {id ? (
                            <button
                              type="button"
                              className="btn btn-danger"
                              disabled={Boolean(deletingId)}
                              onClick={() => onDelete(doc)}
                              aria-label={`Delete ${doc.filename || id}`}
                            >
                              {deletingId === id ? "Deleting..." : "Delete"}
                            </button>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}
