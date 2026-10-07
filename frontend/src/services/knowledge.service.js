import { apiRequest } from "./apiClient";
import { getStoredToken } from "../utils/storage";

export function uploadDocument(formData) {
  return apiRequest("/api/knowledge/upload", {
    method: "POST",
    body: formData,
    isFormData: true,
    token: getStoredToken(),
  });
}

export function listDocuments() {
  return apiRequest("/api/knowledge/documents", {
    method: "GET",
    token: getStoredToken(),
  });
}

export function deleteDocument(documentId) {
  return apiRequest(`/api/knowledge/documents/${documentId}`, {
    method: "DELETE",
    token: getStoredToken(),
  });
}
