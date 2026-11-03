import { api } from "./client";

const TOKEN_KEY = "ww-auth-token";
const USER_KEY  = "ww-user";

// ── token helpers ──────────────────────────────────────────────────────────

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function signup(name, email, password) {
  const res = await fetch(
    (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/auth/signup",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Signup failed");
  }
  const data = await res.json();
  saveToken(data.access_token);
  saveUser(data.user);
  return data.user;
}

export async function login(email, password) {
  const res = await fetch(
    (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/auth/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login failed");
  }
  const data = await res.json();
  saveToken(data.access_token);
  saveUser(data.user);
  return data.user;
}

export async function getMe() {
  const token = getToken();
  if (!token) return null;
  const res = await fetch(
    (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/auth/me",
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) return null;
  const user = await res.json();
  saveUser(user);
  return user;
}

export async function updateProfile(updates) {
  const token = getToken();
  const res = await fetch(
    (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/auth/profile",
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Profile update failed");
  }
  const user = await res.json();
  saveUser(user);
  return user;
}

export function logout() {
  clearToken();
}
