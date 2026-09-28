import { SESSION_TOKEN_KEY, SESSION_USER_KEY } from "./constants";

export function getStoredToken() {
  return window.localStorage.getItem(SESSION_TOKEN_KEY);
}

export function getStoredUser() {
  const raw = window.localStorage.getItem(SESSION_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setSession(token, user) {
  window.localStorage.setItem(SESSION_TOKEN_KEY, token);
  window.localStorage.setItem(SESSION_USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  window.localStorage.removeItem(SESSION_TOKEN_KEY);
  window.localStorage.removeItem(SESSION_USER_KEY);
}
