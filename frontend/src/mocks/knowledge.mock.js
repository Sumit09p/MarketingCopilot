import { delay } from "./delay";
import documentsData from "./data/documents.json";

const documents = JSON.parse(JSON.stringify(documentsData));

export async function uploadDocument() {
  await delay();
  return {
    document_id: `document_${Date.now()}`,
    filename: "uploaded-file.pdf",
    status: "PROCESSING",
  };
}

export async function listDocuments() {
  await delay();
  return documents.map((item) => ({ ...item }));
}

export async function deleteDocument(documentId) {
  await delay();
  const index = documents.findIndex((item) => item.id === documentId);
  if (index >= 0) documents.splice(index, 1);
  return null;
}
