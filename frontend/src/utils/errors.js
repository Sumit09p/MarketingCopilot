import { ApiError } from "../services/apiClient";

export function getUserFacingError(error, fallback = "Something went wrong. Please try again.") {
  if (!error) return fallback;

  if (error instanceof ApiError) {
    if (error.status === 401) {
      return error.message || "Authentication required";
    }
    if (error.status === 403) {
      return "You do not have permission to do that.";
    }
    if (error.status === 422) {
      return error.message || "Please check your details and try again.";
    }
    return error.message || fallback;
  }

  const message = String(error.message || "");
  if (/failed to fetch|networkerror|load failed/i.test(message)) {
    return "Unable to reach the server. Please try again.";
  }

  return fallback;
}
