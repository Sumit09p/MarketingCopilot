export class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status ?? 500;
    this.data = data ?? null;
  }
}

function getBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
}

async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, token, headers = {}, isFormData = false } = options;
  const requestHeaders = { ...headers };

  if (!isFormData && body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
  }

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${getBaseUrl()}${path}`, {
    method,
    headers: requestHeaders,
    body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  const payload = await parseBody(response);

  if (!response.ok) {
    const message =
      payload?.message ||
      (response.status === 401
        ? "Authentication required"
        : response.status === 403
          ? "Permission denied"
          : response.status === 422
            ? "Validation error"
            : `Request failed (${response.status})`);

    throw new ApiError(message, { status: response.status, data: payload });
  }

  if (payload && typeof payload === "object" && "success" in payload) {
    if (payload.success === false) {
      throw new ApiError(payload.message || "Request failed", {
        status: response.status,
        data: payload.data ?? null,
      });
    }
    return payload.data;
  }

  return payload;
}

export const apiClient = {
  get: (path, options) => apiRequest(path, { ...options, method: "GET" }),
  post: (path, body, options) => apiRequest(path, { ...options, method: "POST", body }),
  put: (path, body, options) => apiRequest(path, { ...options, method: "PUT", body }),
  patch: (path, body, options) => apiRequest(path, { ...options, method: "PATCH", body }),
  delete: (path, options) => apiRequest(path, { ...options, method: "DELETE" }),
};
