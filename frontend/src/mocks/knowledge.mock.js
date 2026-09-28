import { delay } from "./delay";
import documentsData from "./data/documents.json";

const documents = JSON.parse(JSON.stringify(documentsData));
const sessionStarted = new Map();

function publicDocument(item) {
  const { session_upload, ...rest } = item;
  void session_upload;
  return { ...rest };
}

function fileFromFormData(formData) {
  if (!formData || typeof formData.get !== "function") return null;
  return formData.get("file");
}

export async function uploadDocument(formData) {
  await delay();
  const file = fileFromFormData(formData);
  const filename = file && typeof file === "object" && file.name ? file.name : "uploaded-file.pdf";
  const extension = String(filename.split(".").pop() || "pdf").toUpperCase();
  const id = `document_${Date.now()}`;
  const item = {
    id,
    filename,
    type: extension,
    status: "PROCESSING",
    uploaded_at: new Date().toISOString(),
    size: typeof file?.size === "number" ? file.size : undefined,
    session_upload: true,
  };
  documents.unshift(item);
  sessionStarted.set(id, Date.now());
  return {
    document_id: id,
    filename,
    status: "PROCESSING",
  };
}

export async function listDocuments() {
  await delay();
  const now = Date.now();
  documents.forEach((item) => {
    if (item.status !== "PROCESSING" || !item.session_upload) return;
    const started = sessionStarted.get(item.id) || new Date(item.uploaded_at).getTime();
    if (now - started >= 4000) {
      item.status = "READY";
    }
  });
  return documents.map(publicDocument);
}

export async function deleteDocument(documentId) {
  await delay();
  const index = documents.findIndex((item) => item.id === documentId);
  if (index >= 0) {
    documents.splice(index, 1);
    sessionStarted.delete(documentId);
  }
  return null;
}
