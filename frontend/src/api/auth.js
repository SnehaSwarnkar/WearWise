import { getCsrfToken, getStoreApiBase } from "./client";

function cleanErrorDetail(err, fallback) {
  if (!err || !err.detail) return fallback;
  if (typeof err.detail === "string") return err.detail;
  if (typeof err.detail === "object" && err.detail.message) return err.detail.message;
  return fallback;
}

async function authFetch(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { ...(options.headers || {}) };
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf && !headers["X-CSRF-Token"]) {
      headers["X-CSRF-Token"] = csrf;
    }
  }
  return fetch(`${getStoreApiBase()}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });
}

// Clear any legacy localStorage token remnants safely (auth now uses HTTP-only cookies)
export function clearLegacyAuthStorage() {
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem("ww-auth-token");
    localStorage.removeItem("ww-user");
    localStorage.removeItem("wearwise_jwt");
    localStorage.removeItem("wearwise_role");
  }
}

export function getToken() {
  return null;
}

export function getStoredUser() {
  return null;
}

export function saveUser() {
  // User session is authoritative via server /api/auth/me HTTP-only cookie
}

// ── Shopper & Seller API calls ─────────────────────────────────────────────

export async function signup(name, email, password) {
  const res = await authFetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(cleanErrorDetail(err, "Signup failed"));
  }
  const data = await res.json();
  clearLegacyAuthStorage();
  return data.user;
}

export async function login(email, password) {
  const res = await authFetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(cleanErrorDetail(err, "Login failed"));
  }
  const data = await res.json();
  clearLegacyAuthStorage();
  return data.user;
}

export async function sellerLogin(email, password) {
  const res = await authFetch("/api/auth/seller/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(cleanErrorDetail(err, "Seller login failed"));
  }
  const data = await res.json();
  clearLegacyAuthStorage();
  return data.user;
}

export async function adminLogin(email, password) {
  const res = await authFetch("/api/auth/admin/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(cleanErrorDetail(err, "Administrator login failed"));
  }
  const data = await res.json();
  clearLegacyAuthStorage();
  return data.user;
}

export async function applyForSeller(payload) {
  const res = await authFetch("/api/auth/seller/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(cleanErrorDetail(err, "Seller onboarding application failed"));
  }
  return res.json();
}

export async function getMe() {
  const res = await authFetch("/api/auth/me");
  if (!res.ok) return null;
  const data = await res.json().catch(() => null);
  if (!data || !data.id || !data.email) return null;
  return data;
}

export async function updateProfile(updates) {
  const res = await authFetch("/api/auth/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(cleanErrorDetail(err, "Profile update failed"));
  }
  return res.json();
}

export async function logout() {
  try {
    await authFetch("/api/auth/logout", { method: "POST" });
  } catch {
    // Best-effort clear even if network unavailable
  }
  clearLegacyAuthStorage();
}
