/**
 * Base API client for WearWise.
 * All calls go to the FastAPI backend at http://localhost:8000.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Returns a stable anonymous session ID for this browser session.
 * Stored in sessionStorage so it resets when the tab closes.
 * Swap for a real auth token when you add user accounts.
 */
export function getSessionId() {
  let id = sessionStorage.getItem("ww-session-id");
  if (!id) {
    id = "sess_" + Math.random().toString(36).slice(2, 11);
    sessionStorage.setItem("ww-session-id", id);
  }
  return id;
}

async function request(method, path, body = null, isFormData = false) {
  const headers = {};
  if (body && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body
      ? isFormData
        ? body
        : JSON.stringify(body)
      : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }

  return res.json();
}

export const api = {
  get:    (path)              => request("GET",    path),
  post:   (path, body)        => request("POST",   path, body),
  put:    (path, body)        => request("PUT",    path, body),
  patch:  (path, body)        => request("PATCH",  path, body),
  delete: (path)              => request("DELETE", path),
  form:   (path, formData)    => request("POST",   path, formData, true),
};
